from __future__ import annotations

from httpx import ASGITransport, AsyncClient
import pytest

from app import main as main_module
from app.core import config as config_module
from app.core import database as database_module
from app.routers import api as api_module
from app.routers import user as user_router_module
from app.schemas.user import UserCreate
from app.services import user as user_service_module
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

        _, database, _, user_service, _, main = self.reload_modules(
            config_module,
            database_module,
            user_router_module,
            user_service_module,
            api_module,
            main_module,
        )

        app = main.create_app()
        transport = ASGITransport(app=app)

        await database.create_db_and_tables()
        try:
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                async with database.async_session_maker() as session:
                    await user_service.create_user(
                        session,
                        UserCreate(
                            username="moluo",
                            nickname="Moluo",
                            email="moluo@example.com",
                            password="password123",
                            repassword="password123",
                        ),
                    )

                login_response = await client.post(
                    "/api/users/login",
                    json={"username": "moluo", "password": "password123"},
                )
                assert login_response.status_code == 200
                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                list_response = await client.get("/api/users/", headers=headers)
                assert list_response.status_code == 200
                usernames = [user["username"] for user in list_response.json()]
                assert "moluo" in usernames

                create_response = await client.post(
                    "/api/users/",
                    json={
                        "username": "newuser",
                        "nickname": "New",
                        "email": "new@example.com",
                        "password": "password123",
                        "repassword": "password123",
                    },
                    headers=headers,
                )
                assert create_response.status_code == 201
                created_user = create_response.json()
                public_id = created_user["public_id"]

                detail_response = await client.get(f"/api/users/{public_id}", headers=headers)
                assert detail_response.status_code == 200
                assert detail_response.json()["email"] == "new@example.com"

                update_response = await client.put(
                    f"/api/users/{public_id}",
                    json={"nickname": "New Updated"},
                    headers=headers,
                )
                assert update_response.status_code == 200
                assert update_response.json()["nickname"] == "New Updated"

                disable_response = await client.patch(
                    f"/api/users/{public_id}/disable", headers=headers
                )
                assert disable_response.status_code == 200
                assert disable_response.json()["disabled_at"] is not None

                delete_response = await client.delete(
                    f"/api/users/{public_id}", headers=headers
                )
                assert delete_response.status_code == 204

                missing_response = await client.get(
                    f"/api/users/{public_id}", headers=headers
                )
                assert missing_response.status_code == 404
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()