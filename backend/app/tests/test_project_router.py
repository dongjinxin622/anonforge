from __future__ import annotations

from httpx import ASGITransport, AsyncClient
import pytest

from app import main as main_module
from app.core import config as config_module
from app.core import database as database_module
from app.routers import api as api_module
from app.routers import project as project_router_module
from app.routers import user as user_router_module
from app.tests.base import EnvTestBase


class TestProjectRouter(EnvTestBase):
    async def _login(self, client: AsyncClient, username: str, password: str) -> str:
        response = await client.post(
            "/api/users/login",
            json={"username": username, "password": password},
        )
        assert response.status_code == 200, f"登录失败: {response.status_code} {response.text}"
        return response.json()["access_token"]

    def _auth_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.anyio
    async def test_project_router_crud_flow(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "router_project.db"),
            },
        )

        _, database, _, _, _, main = self.reload_modules(
            config_module,
            database_module,
            user_router_module,
            project_router_module,
            api_module,
            main_module,
        )

        app = main.create_app()
        transport = ASGITransport(app=app)

        await database.create_db_and_tables()
        try:
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                create_user_resp = await client.post(
                    "/api/users/",
                    json={
                        "username": "owner",
                        "nickname": "Owner",
                        "email": "owner@test.com",
                        "password": "password123",
                        "repassword": "password123",
                    },
                )
                assert create_user_resp.status_code == 201, f"创建用户失败: {create_user_resp.status_code} {create_user_resp.text}"
                token = await self._login(client, "owner", "password123")
                headers = self._auth_headers(token)

                create_response = await client.post(
                    "/api/projects/",
                    json={
                        "name": "API测试项目",
                        "intro": "通过接口创建的项目",
                    },
                    headers=headers,
                )
                assert create_response.status_code == 201
                project = create_response.json()
                assert project["name"] == "API测试项目"
                public_id = project["public_id"]

                list_response = await client.get(
                    "/api/projects/",
                    headers=headers,
                )
                assert list_response.status_code == 200
                assert len(list_response.json()) == 1

                detail_response = await client.get(
                    f"/api/projects/{public_id}",
                    headers=headers,
                )
                assert detail_response.status_code == 200
                assert detail_response.json()["intro"] == "通过接口创建的项目"

                search_response = await client.get(
                    "/api/projects/search/by-name",
                    params={"name": "API"},
                    headers=headers,
                )
                assert search_response.status_code == 200
                assert len(search_response.json()) == 1

                search_member_response = await client.get(
                    "/api/projects/search/by-member",
                    params={"member_public_id": project["owner_id"]},
                    headers=headers,
                )
                assert search_member_response.status_code == 200
                assert len(search_member_response.json()) == 1

                update_response = await client.put(
                    f"/api/projects/{public_id}",
                    json={"name": "更新后的项目", "intro": "已通过接口更新"},
                    headers=headers,
                )
                assert update_response.status_code == 200
                assert update_response.json()["name"] == "更新后的项目"

                disable_response = await client.patch(
                    f"/api/projects/{public_id}/disable",
                    headers=headers,
                )
                assert disable_response.status_code == 200
                assert disable_response.json()["disabled_at"] is not None

                enable_response = await client.patch(
                    f"/api/projects/{public_id}/enable",
                    headers=headers,
                )
                assert enable_response.status_code == 200
                assert enable_response.json()["disabled_at"] is None

                delete_response = await client.delete(
                    f"/api/projects/{public_id}",
                    headers=headers,
                )
                assert delete_response.status_code == 204

                missing_response = await client.get(
                    f"/api/projects/{public_id}",
                    headers=headers,
                )
                assert missing_response.status_code == 404
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()

    @pytest.mark.anyio
    async def test_project_router_requires_auth(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "router_unauth.db"),
            },
        )

        _, database, _, _, _, main = self.reload_modules(
            config_module,
            database_module,
            user_router_module,
            project_router_module,
            api_module,
            main_module,
        )

        app = main.create_app()
        transport = ASGITransport(app=app)

        await database.create_db_and_tables()
        try:
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                list_response = await client.get("/api/projects/")
                assert list_response.status_code == 401

                create_response = await client.post(
                    "/api/projects/",
                    json={"name": "未认证项目"},
                )
                assert create_response.status_code == 401
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()

    @pytest.mark.anyio
    async def test_project_member_router_flow(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "router_member.db"),
            },
        )

        _, database, _, _, _, main = self.reload_modules(
            config_module,
            database_module,
            user_router_module,
            project_router_module,
            api_module,
            main_module,
        )

        app = main.create_app()
        transport = ASGITransport(app=app)

        await database.create_db_and_tables()
        try:
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                await client.post(
                    "/api/users/",
                    json={
                        "username": "owner2",
                        "nickname": "Owner",
                        "email": "owner2@test.com",
                        "password": "password123",
                        "repassword": "password123",
                    },
                )
                await client.post(
                    "/api/users/",
                    json={
                        "username": "member2",
                        "nickname": "Member",
                        "email": "member2@test.com",
                        "password": "password123",
                        "repassword": "password123",
                    },
                )
                owner_token = await self._login(client, "owner2", "password123")
                owner_headers = self._auth_headers(owner_token)

                create_response = await client.post(
                    "/api/projects/",
                    json={"name": "成员管理项目"},
                    headers=owner_headers,
                )
                project_public_id = create_response.json()["public_id"]

                candidates_response = await client.get(
                    f"/api/projects/{project_public_id}/members/candidates",
                    params={"keyword": "mem"},
                    headers=owner_headers,
                )
                assert candidates_response.status_code == 200
                candidates = candidates_response.json()
                assert len(candidates) > 0
                member_public_id = candidates[0]["public_id"]

                invite_response = await client.post(
                    f"/api/projects/{project_public_id}/members/invitations",
                    json={
                        "user_public_id": member_public_id,
                        "role": "editor",
                    },
                    headers=owner_headers,
                )
                assert invite_response.status_code == 201
                assert invite_response.json()["role"] == "editor"

                members_response = await client.get(
                    f"/api/projects/{project_public_id}/members",
                    headers=owner_headers,
                )
                assert members_response.status_code == 200
                assert len(members_response.json()) == 2

                update_role_response = await client.patch(
                    f"/api/projects/{project_public_id}/members/{member_public_id}",
                    params={"role": "admin"},
                    headers=owner_headers,
                )
                assert update_role_response.status_code == 200
                assert update_role_response.json()["role"] == "admin"

                remove_response = await client.delete(
                    f"/api/projects/{project_public_id}/members/{member_public_id}",
                    headers=owner_headers,
                )
                assert remove_response.status_code == 204

                members_after = await client.get(
                    f"/api/projects/{project_public_id}/members",
                    headers=owner_headers,
                )
                assert len(members_after.json()) == 1

                # 候选列表中已加入的成员不再出现
                candidates_after = await client.get(
                    f"/api/projects/{project_public_id}/members/candidates",
                    params={"keyword": "mem"},
                    headers=owner_headers,
                )
                assert any(c["public_id"] == member_public_id for c in candidates_after.json())
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()