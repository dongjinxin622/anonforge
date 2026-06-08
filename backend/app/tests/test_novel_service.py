from __future__ import annotations

import pytest

from app.core import config as config_module
from app.core import database as database_module
from app.schemas.novel import NovelChapterImport, NovelChapterImportItem
from app.schemas.project import ProjectCreate
from app.schemas.user import UserCreate
from app.services import novel as novel_service_module
from app.services import project as project_service_module
from app.services import user as user_service_module
from app.tests.base import EnvTestBase


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class TestNovelService(EnvTestBase):
    @pytest.mark.anyio
    async def test_import_chapters_accepts_preview_drafts(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        self.set_env(
            monkeypatch,
            {
                "DB_ENGINE": "sqlite",
                "DB_DRIVER": "aiosqlite",
                "DB_SQLITE_PATH": str(tmp_path / "novel-import.db"),
            },
        )

        _, database, user_service, project_service, novel_service = self.reload_modules(
            config_module,
            database_module,
            user_service_module,
            project_service_module,
            novel_service_module,
        )

        await database.create_db_and_tables()
        try:
            async with database.async_session_maker() as session:
                owner = await user_service.create_user(
                    session,
                    UserCreate(
                        username="novel-owner",
                        nickname="Novel Owner",
                        email="novel-owner@example.com",
                        password="password123",
                        repassword="password123",
                    ),
                )
                project = await project_service.create_project(
                    session,
                    owner.public_id,
                    ProjectCreate(name="Novel Import Project"),
                )

                imported = await novel_service.import_chapters(
                    session,
                    project.public_id,
                    owner.public_id,
                    NovelChapterImport(
                        chapters=[
                            NovelChapterImportItem(
                                reel="\u7b2c\u4e00\u96c6",
                                chapter="\u5e8f\u7ae0",
                                chapter_data="\u5e8f\u7ae0\u6b63\u6587",
                            ),
                            NovelChapterImportItem(
                                reel="\u7b2c\u4e00\u96c6",
                                chapter="\u7b2c\u4e00\u7ae0 \u9752\u4e91",
                                chapter_data="\u9752\u4e91\u6b63\u6587",
                            ),
                        ],
                    ),
                )

            assert [item.chapter_index for item in imported] == [1, 2]
            assert [item.reel for item in imported] == ["\u7b2c\u4e00\u96c6", "\u7b2c\u4e00\u96c6"]
            assert [item.chapter for item in imported] == [
                "\u5e8f\u7ae0",
                "\u7b2c\u4e00\u7ae0 \u9752\u4e91",
            ]
        finally:
            await database.drop_db_and_tables()
            await database.engine.dispose()
