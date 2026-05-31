from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.middlewares import common
from app.routers.base import BaseView, route
from app.schemas.novel import (
    NovelChapterBatchClean,
    NovelChapterBatchDelete,
    NovelChapterBatchResult,
    NovelChapterCreate,
    NovelChapterEventStateUpdate,
    NovelChapterImport,
    NovelChapterPage,
    NovelChapterRead,
    NovelChapterUpdate,
    NovelImportSplitRule,
)
from app.services import novel as novel_service
from app.services import project as project_service

SessionDep = Annotated[AsyncSession, Depends(get_session)]

NOVEL_ROUTE_MIDDLEWARES = [
    Depends(common.jwt_auth_middleware),
    Depends(common.request_duration_middleware),
]


class NovelView(BaseView):
    """小说章节类视图。"""

    router_prefix = "/projects/{project_public_id}/novels"
    router_tags = ["novel"]

    @staticmethod
    def _current_user_public_id(request: Request) -> str:
        """从已认证请求中读取当前用户公开标识。"""
        public_id = getattr(request.state, "current_user_public_id", None)
        if not public_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="请提供 access token",
                headers=common.BEARER_AUTH_HEADER,
            )
        return str(public_id)

    @staticmethod
    def _raise_as_http(exc: Exception) -> None:
        """将服务层异常转换为 HTTP 异常。"""
        if isinstance(exc, project_service.ProjectNotFoundError):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        if isinstance(exc, project_service.ProjectAccessDeniedError):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        if isinstance(exc, novel_service.NovelChapterNotFoundError):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        if isinstance(exc, novel_service.NovelChapterValidationError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        raise exc

    @route(
        "",
        methods=["GET"],
        response_model=NovelChapterPage,
        middlewares=NOVEL_ROUTE_MIDDLEWARES,
        summary="获取小说章节列表",
        description="按项目公开 ID 分页获取小说章节列表。",
    )
    async def list_chapters(
        self,
        project_public_id: str,
        request: Request,
        session: SessionDep,
        page: int = Query(default=1, ge=1),
        limit: int = Query(default=20, ge=1, le=100),
        search: str = "",
    ) -> NovelChapterPage:
        """获取小说章节列表。"""
        current_user_public_id = self._current_user_public_id(request)
        try:
            return await novel_service.list_chapters(
                session,
                project_public_id,
                current_user_public_id,
                page=page,
                limit=limit,
                search=search,
            )
        except (project_service.ProjectServiceError, novel_service.NovelServiceError) as exc:
            self._raise_as_http(exc)

    @route(
        "",
        methods=["POST"],
        response_model=NovelChapterRead,
        status_code=status.HTTP_201_CREATED,
        middlewares=NOVEL_ROUTE_MIDDLEWARES,
        summary="创建小说章节",
        description="在指定项目下创建小说章节。",
    )
    async def create_chapter(
        self,
        project_public_id: str,
        payload: NovelChapterCreate,
        request: Request,
        session: SessionDep,
    ) -> NovelChapterRead:
        """创建小说章节。"""
        current_user_public_id = self._current_user_public_id(request)
        try:
            return await novel_service.create_chapter(session, project_public_id, current_user_public_id, payload)
        except (project_service.ProjectServiceError, novel_service.NovelServiceError) as exc:
            self._raise_as_http(exc)

    @route(
        "/import",
        methods=["POST"],
        response_model=list[NovelChapterRead],
        status_code=status.HTTP_201_CREATED,
        middlewares=NOVEL_ROUTE_MIDDLEWARES,
        summary="导入小说全文",
        description="将全文按卷和章节拆分后导入指定项目。",
    )
    async def import_chapters(
        self,
        project_public_id: str,
        payload: NovelChapterImport,
        request: Request,
        session: SessionDep,
    ) -> list[NovelChapterRead]:
        """导入小说全文。"""
        current_user_public_id = self._current_user_public_id(request)
        try:
            return await novel_service.import_chapters(session, project_public_id, current_user_public_id, payload)
        except (project_service.ProjectServiceError, novel_service.NovelServiceError) as exc:
            self._raise_as_http(exc)

    @route(
        "/import-split-rules",
        methods=["GET"],
        response_model=list[NovelImportSplitRule],
        middlewares=NOVEL_ROUTE_MIDDLEWARES,
        summary="获取小说导入切分规则",
        description="获取服务端内置的全文导入章节切分规则。",
    )
    async def list_import_split_rules(
        self,
        project_public_id: str,
        request: Request,
        session: SessionDep,
    ) -> list[NovelImportSplitRule]:
        """获取全文导入切分规则。"""
        current_user_public_id = self._current_user_public_id(request)
        try:
            await project_service.get_project_or_raise(session, project_public_id, current_user_public_id)
            return novel_service.list_import_split_rules()
        except (project_service.ProjectServiceError, novel_service.NovelServiceError) as exc:
            self._raise_as_http(exc)

    @route(
        "/batch-delete",
        methods=["POST"],
        response_model=NovelChapterBatchResult,
        middlewares=NOVEL_ROUTE_MIDDLEWARES,
        summary="批量删除小说章节",
        description="按章节 ID 批量删除指定项目下的小说章节。",
    )
    async def batch_delete_chapters(
        self,
        project_public_id: str,
        payload: NovelChapterBatchDelete,
        request: Request,
        session: SessionDep,
    ) -> NovelChapterBatchResult:
        """批量删除小说章节。"""
        current_user_public_id = self._current_user_public_id(request)
        try:
            return await novel_service.batch_delete_chapters(
                session,
                project_public_id,
                current_user_public_id,
                payload,
            )
        except (project_service.ProjectServiceError, novel_service.NovelServiceError) as exc:
            self._raise_as_http(exc)

    @route(
        "/batch-clean",
        methods=["POST"],
        response_model=NovelChapterBatchResult,
        middlewares=NOVEL_ROUTE_MIDDLEWARES,
        summary="批量清洗章节事件",
        description="按章节 ID 批量生成事件清洗结果。",
    )
    async def batch_clean_chapters(
        self,
        project_public_id: str,
        payload: NovelChapterBatchClean,
        request: Request,
        session: SessionDep,
    ) -> NovelChapterBatchResult:
        """批量清洗章节事件。"""
        current_user_public_id = self._current_user_public_id(request)
        try:
            return await novel_service.batch_clean_chapters(
                session,
                project_public_id,
                current_user_public_id,
                payload,
            )
        except (project_service.ProjectServiceError, novel_service.NovelServiceError) as exc:
            self._raise_as_http(exc)

    @route(
        "/event-state",
        methods=["POST"],
        response_model=NovelChapterBatchResult,
        middlewares=NOVEL_ROUTE_MIDDLEWARES,
        summary="批量更新章节事件状态",
        description="按章节 ID 批量更新事件清洗状态。",
    )
    async def update_event_state(
        self,
        project_public_id: str,
        payload: NovelChapterEventStateUpdate,
        request: Request,
        session: SessionDep,
    ) -> NovelChapterBatchResult:
        """批量更新章节事件状态。"""
        current_user_public_id = self._current_user_public_id(request)
        try:
            return await novel_service.update_event_state(session, project_public_id, current_user_public_id, payload)
        except (project_service.ProjectServiceError, novel_service.NovelServiceError) as exc:
            self._raise_as_http(exc)

    @route(
        "/{chapter_id}",
        methods=["PUT"],
        response_model=NovelChapterRead,
        middlewares=NOVEL_ROUTE_MIDDLEWARES,
        summary="更新小说章节",
        description="更新指定项目下的单个小说章节。",
    )
    async def update_chapter(
        self,
        project_public_id: str,
        chapter_id: int,
        payload: NovelChapterUpdate,
        request: Request,
        session: SessionDep,
    ) -> NovelChapterRead:
        """更新小说章节。"""
        current_user_public_id = self._current_user_public_id(request)
        try:
            return await novel_service.update_chapter(
                session,
                project_public_id,
                chapter_id,
                current_user_public_id,
                payload,
            )
        except (project_service.ProjectServiceError, novel_service.NovelServiceError) as exc:
            self._raise_as_http(exc)

    @route(
        "/{chapter_id}",
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
        middlewares=NOVEL_ROUTE_MIDDLEWARES,
        summary="删除小说章节",
        description="删除指定项目下的单个小说章节。",
    )
    async def delete_chapter(
        self,
        project_public_id: str,
        chapter_id: int,
        request: Request,
        session: SessionDep,
    ) -> Response:
        """删除小说章节。"""
        current_user_public_id = self._current_user_public_id(request)
        try:
            await novel_service.delete_chapter(session, project_public_id, chapter_id, current_user_public_id)
        except (project_service.ProjectServiceError, novel_service.NovelServiceError) as exc:
            self._raise_as_http(exc)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @route(
        "/{chapter_id}/clean",
        methods=["POST"],
        response_model=NovelChapterRead,
        middlewares=NOVEL_ROUTE_MIDDLEWARES,
        summary="清洗章节事件",
        description="为指定项目下的单个章节生成事件清洗结果。",
    )
    async def clean_chapter(
        self,
        project_public_id: str,
        chapter_id: int,
        request: Request,
        session: SessionDep,
    ) -> NovelChapterRead:
        """清洗章节事件。"""
        current_user_public_id = self._current_user_public_id(request)
        try:
            return await novel_service.clean_chapter(session, project_public_id, chapter_id, current_user_public_id)
        except (project_service.ProjectServiceError, novel_service.NovelServiceError) as exc:
            self._raise_as_http(exc)


router = NovelView()()
