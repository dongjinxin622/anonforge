from __future__ import annotations

import pytest

from app.core import config as config_module
from app.core import database as database_module
from app.models.project import ProjectMemberRole
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services import project as project_service_module
from app.services import user as user_service_module
from app.schemas.user import UserCreate
from app.tests.base import EnvTestBase


class TestProjectService(EnvTestBase):
    @pytest.mark.anyio
    async def test_project_crud_flow(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "project_crud.db"),
            },
        )

        _, database, user_service, project_service = self.reload_modules(
            config_module,
            database_module,
            user_service_module,
            project_service_module,
        )

        await database.create_db_and_tables()
        try:
            async with database.async_session_maker() as session:
                owner = await user_service.create_user(
                    session,
                    UserCreate(
                        username="owner",
                        nickname="Owner",
                        email="owner@example.com",
                        password="password123",
                        repassword="password123",
                    ),
                )

            async with database.async_session_maker() as session:
                project = await project_service.create_project(
                    session,
                    owner.public_id,
                    ProjectCreate(
                        name="测试项目",
                        intro="一个测试项目",
                        project_type="original_script",
                    ),
                )
                assert project.id is not None
                assert project.name == "测试项目"
                assert project.owner_id == owner.public_id

            async with database.async_session_maker() as session:
                projects = await project_service.list_projects(session, owner.public_id)
                assert len(projects) == 1
                assert projects[0].public_id == project.public_id

            async with database.async_session_maker() as session:
                detail = await project_service.get_project_or_raise(
                    session,
                    project.public_id,
                    owner.public_id,
                )
                assert detail.name == "测试项目"

            async with database.async_session_maker() as session:
                result = await project_service.search_projects_by_name(
                    session,
                    owner.public_id,
                    "测试",
                )
                assert len(result) == 1

            async with database.async_session_maker() as session:
                updated = await project_service.update_project(
                    session,
                    project.public_id,
                    ProjectUpdate(name="更新项目", intro="已更新"),
                    owner.public_id,
                )
                assert updated.name == "更新项目"
                assert updated.intro == "已更新"

            async with database.async_session_maker() as session:
                disabled = await project_service.disable_project(
                    session,
                    project.public_id,
                    owner.public_id,
                )
                assert disabled.disabled_at is not None

            async with database.async_session_maker() as session:
                enabled = await project_service.enable_project(
                    session,
                    project.public_id,
                    owner.public_id,
                )
                assert enabled.disabled_at is None

            async with database.async_session_maker() as session:
                await project_service.delete_project(
                    session,
                    project.public_id,
                    owner.public_id,
                )
                with pytest.raises(project_service_module.ProjectNotFoundError):
                    await project_service.get_project_or_raise(
                        session,
                        project.public_id,
                        owner.public_id,
                    )
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()

    @pytest.mark.anyio
    async def test_project_access_denied_for_non_member(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "access_denied.db"),
            },
        )

        _, database, user_service, project_service = self.reload_modules(
            config_module,
            database_module,
            user_service_module,
            project_service_module,
        )

        await database.create_db_and_tables()
        try:
            async with database.async_session_maker() as session:
                owner = await user_service.create_user(
                    session,
                    UserCreate(
                        username="owner",
                        nickname="Owner",
                        email="owner@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )
                intruder = await user_service.create_user(
                    session,
                    UserCreate(
                        username="intruder",
                        nickname="Intruder",
                        email="intruder@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )

            async with database.async_session_maker() as session:
                project = await project_service.create_project(
                    session,
                    owner.public_id,
                    ProjectCreate(name="私有项目"),
                )

            async with database.async_session_maker() as session:
                with pytest.raises(project_service_module.ProjectAccessDeniedError):
                    await project_service.get_project_or_raise(
                        session,
                        project.public_id,
                        intruder.public_id,
                    )
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()

    @pytest.mark.anyio
    async def test_superuser_can_access_any_project(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "superuser.db"),
            },
        )

        _, database, user_service, project_service = self.reload_modules(
            config_module,
            database_module,
            user_service_module,
            project_service_module,
        )

        await database.create_db_and_tables()
        try:
            async with database.async_session_maker() as session:
                owner = await user_service.create_user(
                    session,
                    UserCreate(
                        username="owner",
                        nickname="Owner",
                        email="owner@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )
                admin = await user_service.create_user(
                    session,
                    UserCreate(
                        username="admin_user",
                        nickname="Admin",
                        email="admin@e.com",
                        password="password123",
                        repassword="password123",
                        is_superuser=True,
                    ),
                )

            async with database.async_session_maker() as session:
                project = await project_service.create_project(
                    session,
                    owner.public_id,
                    ProjectCreate(name="超级管理员可见项目"),
                )

            async with database.async_session_maker() as session:
                detail = await project_service.get_project_or_raise(
                    session,
                    project.public_id,
                    admin.public_id,
                )
                assert detail.name == "超级管理员可见项目"
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()

    @pytest.mark.anyio
    async def test_project_member_management(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "member.db"),
            },
        )

        _, database, user_service, project_service = self.reload_modules(
            config_module,
            database_module,
            user_service_module,
            project_service_module,
        )

        await database.create_db_and_tables()
        try:
            async with database.async_session_maker() as session:
                owner = await user_service.create_user(
                    session,
                    UserCreate(
                        username="owner",
                        nickname="Owner",
                        email="owner@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )
                member = await user_service.create_user(
                    session,
                    UserCreate(
                        username="member",
                        nickname="Member",
                        email="member@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )

            async with database.async_session_maker() as session:
                project = await project_service.create_project(
                    session,
                    owner.public_id,
                    ProjectCreate(name="团队项目"),
                )

            async with database.async_session_maker() as session:
                added = await project_service.add_project_member(
                    session,
                    project.public_id,
                    member.public_id,
                    ProjectMemberRole.EDITOR,
                    owner.public_id,
                )
                assert added.role == ProjectMemberRole.EDITOR
                assert added.user_public_id == member.public_id

            async with database.async_session_maker() as session:
                members = await project_service.list_project_members(
                    session,
                    project.public_id,
                    owner.public_id,
                )
                assert len(members) == 2

            async with database.async_session_maker() as session:
                updated = await project_service.update_project_member_role(
                    session,
                    project.public_id,
                    member.public_id,
                    ProjectMemberRole.ADMIN,
                    owner.public_id,
                )
                assert updated.role == ProjectMemberRole.ADMIN

            async with database.async_session_maker() as session:
                await project_service.remove_project_member(
                    session,
                    project.public_id,
                    member.public_id,
                    owner.public_id,
                )
                members = await project_service.list_project_members(
                    session,
                    project.public_id,
                    owner.public_id,
                )
                assert len(members) == 1

            async with database.async_session_maker() as session:
                with pytest.raises(project_service_module.ProjectMemberConflictError):
                    await project_service.add_project_member(
                        session,
                        project.public_id,
                        owner.public_id,
                        ProjectMemberRole.EDITOR,
                        owner.public_id,
                    )
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()

    @pytest.mark.anyio
    async def test_member_can_access_project(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "member_access.db"),
            },
        )

        _, database, user_service, project_service = self.reload_modules(
            config_module,
            database_module,
            user_service_module,
            project_service_module,
        )

        await database.create_db_and_tables()
        try:
            async with database.async_session_maker() as session:
                owner = await user_service.create_user(
                    session,
                    UserCreate(
                        username="owner",
                        nickname="Owner",
                        email="owner@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )
                editor = await user_service.create_user(
                    session,
                    UserCreate(
                        username="editor",
                        nickname="Editor",
                        email="editor@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )

            async with database.async_session_maker() as session:
                project = await project_service.create_project(
                    session,
                    owner.public_id,
                    ProjectCreate(name="共享项目"),
                )
                await project_service.add_project_member(
                    session,
                    project.public_id,
                    editor.public_id,
                    ProjectMemberRole.EDITOR,
                    owner.public_id,
                )

            async with database.async_session_maker() as session:
                projects = await project_service.list_projects(session, editor.public_id)
                assert len(projects) == 1
                assert projects[0].name == "共享项目"

            async with database.async_session_maker() as session:
                detail = await project_service.get_project_or_raise(
                    session,
                    project.public_id,
                    editor.public_id,
                )
                assert detail.name == "共享项目"
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()

    @pytest.mark.anyio
    async def test_invite_project_member(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "invite.db"),
            },
        )

        _, database, user_service, project_service = self.reload_modules(
            config_module,
            database_module,
            user_service_module,
            project_service_module,
        )

        await database.create_db_and_tables()
        try:
            async with database.async_session_maker() as session:
                owner = await user_service.create_user(
                    session,
                    UserCreate(
                        username="owner",
                        nickname="Owner",
                        email="owner@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )
                invitee = await user_service.create_user(
                    session,
                    UserCreate(
                        username="invitee",
                        nickname="Invitee",
                        email="invitee@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )

            async with database.async_session_maker() as session:
                project = await project_service.create_project(
                    session,
                    owner.public_id,
                    ProjectCreate(name="邀请测试项目"),
                )

            async with database.async_session_maker() as session:
                result = await project_service.invite_project_member(
                    session,
                    project.public_id,
                    invitee.public_id,
                    ProjectMemberRole.VIEWER,
                    owner.public_id,
                )
                assert result.role == ProjectMemberRole.VIEWER
                assert result.user_public_id == invitee.public_id

            with pytest.raises(project_service_module.ProjectMemberConflictError):
                async with database.async_session_maker() as session:
                    await project_service.invite_project_member(
                        session,
                        project.public_id,
                        invitee.public_id,
                        ProjectMemberRole.VIEWER,
                        owner.public_id,
                    )
                    await session.rollback()
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()

    @pytest.mark.anyio
    async def test_search_member_candidates(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "candidates.db"),
            },
        )

        _, database, user_service, project_service = self.reload_modules(
            config_module,
            database_module,
            user_service_module,
            project_service_module,
        )

        await database.create_db_and_tables()
        try:
            async with database.async_session_maker() as session:
                owner = await user_service.create_user(
                    session,
                    UserCreate(
                        username="owner",
                        nickname="Owner",
                        email="owner@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )
                candidate = await user_service.create_user(
                    session,
                    UserCreate(
                        username="candidate1",
                        nickname="Candidate",
                        email="c1@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )

            async with database.async_session_maker() as session:
                project = await project_service.create_project(
                    session,
                    owner.public_id,
                    ProjectCreate(name="搜索候选项目"),
                )

            async with database.async_session_maker() as session:
                candidates = await project_service.search_project_member_candidates(
                    session,
                    project.public_id,
                    "candidate",
                    owner.public_id,
                )
                assert len(candidates) == 1
                assert candidates[0].username == "candidate1"

                candidates_empty = await project_service.search_project_member_candidates(
                    session,
                    project.public_id,
                    "",
                    owner.public_id,
                )
                assert len(candidates_empty) == 0

            async with database.async_session_maker() as session:
                await project_service.add_project_member(
                    session,
                    project.public_id,
                    candidate.public_id,
                    ProjectMemberRole.EDITOR,
                    owner.public_id,
                )
                candidates_after = await project_service.search_project_member_candidates(
                    session,
                    project.public_id,
                    "candidate",
                    owner.public_id,
                )
                assert len(candidates_after) == 0
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()

    @pytest.mark.anyio
    async def test_search_projects_by_member(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "search_by_member.db"),
            },
        )

        _, database, user_service, project_service = self.reload_modules(
            config_module,
            database_module,
            user_service_module,
            project_service_module,
        )

        await database.create_db_and_tables()
        try:
            async with database.async_session_maker() as session:
                owner = await user_service.create_user(
                    session,
                    UserCreate(
                        username="owner",
                        nickname="Owner",
                        email="owner@e.com",
                        password="password123",
                        repassword="password123",
                    ),
                )

            async with database.async_session_maker() as session:
                project = await project_service.create_project(
                    session,
                    owner.public_id,
                    ProjectCreate(name="按成员搜索项目"),
                )

            async with database.async_session_maker() as session:
                result = await project_service.search_projects_by_member(
                    session,
                    owner.public_id,
                    owner.public_id,
                )
                assert len(result) == 1
                assert result[0].name == "按成员搜索项目"
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()