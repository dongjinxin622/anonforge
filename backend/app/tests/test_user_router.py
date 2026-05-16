from __future__ import annotations

from httpx import ASGITransport, AsyncClient
import pytest

from app import main as main_module
from app.core import config as config_module
from app.core import database as database_module
from app.routers import api as api_module
from app.routers import user as user_router_module
from app.tests.base import EnvTestBase


class TestUserRouter(EnvTestBase):
    @pytest.mark.anyio
    async def test_user_router_runs_with_async_session(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "router.db"),
            },
        )

        _, database, _, _, main = self.reload_modules(
            config_module,
            database_module,
            user_router_module,
            api_module,
            main_module,
        )

        app = main.create_app()
        transport = ASGITransport(app=app)

        await database.create_db_and_tables()
        try:
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                create_response = await client.post(
                    "/api/users/",
                    json={
                        "username": "moluo",
                        "nickname": "Moluo",
                        "email": "moluo@example.com",
                        "password": "password123",
                        "repassword": "password123",
                    },
                )
                assert create_response.status_code == 201
                created_user = create_response.json()
                public_id = created_user["public_id"]

                list_response = await client.get("/api/users/")
                assert list_response.status_code == 200
                assert [user["username"] for user in list_response.json()] == ["moluo"]

                detail_response = await client.get(f"/api/users/{public_id}")
                assert detail_response.status_code == 200
                assert detail_response.json()["email"] == "moluo@example.com"

                update_response = await client.put(
                    f"/api/users/{public_id}",
                    json={"nickname": "Moluo Updated"},
                )
                assert update_response.status_code == 200
                assert update_response.json()["nickname"] == "Moluo Updated"

                disable_response = await client.patch(f"/api/users/{public_id}/disable")
                assert disable_response.status_code == 200
                assert disable_response.json()["disabled_at"] is not None

                delete_response = await client.delete(f"/api/users/{public_id}")
                assert delete_response.status_code == 204

                missing_response = await client.get(f"/api/users/{public_id}")
                assert missing_response.status_code == 404
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()