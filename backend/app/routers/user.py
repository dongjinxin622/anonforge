from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.routers.base import BaseView, route
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user as user_service

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class UserView(BaseView):
    """用户类视图。"""

    router_prefix = "/users"
    router_tags = ["user"]

    @staticmethod
    def _raise_as_http(exc: Exception) -> None:
        """将服务层异常转换为 HTTP 异常。

        Args:
            exc: 服务层抛出的异常对象。

        Raises:
            HTTPException: 对应的 HTTP 错误。
        """
        if isinstance(exc, user_service.UserNotFoundError):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        if isinstance(exc, user_service.UserNameConflictError):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        if isinstance(exc, user_service.UserEmailConflictError):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        raise exc

    @route(
        "/",
        methods=["GET"],
        response_model=list[UserRead],
        summary="获取用户列表",
        description="返回当前系统中的全部用户记录，按排序值和内部主键升序排列。",
    )
    async def list_users(self, session: SessionDep) -> list[UserRead]:
        """获取用户列表。

        Args:
            session: 当前数据库会话依赖。

        Returns:
            list[UserRead]: 用户列表结果。
        """
        return await user_service.list_users(session)

    @route(
        "/{public_id}",
        methods=["GET"],
        response_model=UserRead,
        summary="获取用户详情",
        description="根据用户公开 ID 查询单个用户的详细信息。",
    )
    async def get_user_detail(self, public_id: str, session: SessionDep) -> UserRead:
        """获取用户详情。

        Args:
            public_id: 对外公开的用户标识。
            session: 当前数据库会话依赖。

        Returns:
            UserRead: 用户详情对象。
        """
        try:
            return await user_service.get_user_or_raise(session, public_id)
        except user_service.UserServiceError as exc:
            self._raise_as_http(exc)

    @route(
        "/",
        methods=["POST"],
        response_model=UserRead,
        status_code=status.HTTP_201_CREATED,
        summary="创建用户",
        description="创建新的用户记录，数据库自动生成整数主键，并对外返回 public_id。",
    )
    async def create_user(self, payload: UserCreate, session: SessionDep) -> UserRead:
        """创建用户。

        Args:
            payload: 用户创建请求体。
            session: 当前数据库会话依赖。

        Returns:
            UserRead: 新创建的用户对象。
        """
        try:
            return await user_service.create_user(session, payload)
        except user_service.UserServiceError as exc:
            self._raise_as_http(exc)

    @route(
        "/{public_id}",
        methods=["PUT"],
        response_model=UserRead,
        summary="更新用户",
        description="根据用户公开 ID 更新用户基础资料、密码、排序和账号状态等可编辑字段。",
    )
    async def update_user(self, public_id: str, payload: UserUpdate, session: SessionDep) -> UserRead:
        """更新用户信息。

        Args:
            public_id: 对外公开的用户标识。
            payload: 用户更新请求体。
            session: 当前数据库会话依赖。

        Returns:
            UserRead: 更新后的用户对象。
        """
        try:
            return await user_service.update_user(session, public_id, payload)
        except user_service.UserServiceError as exc:
            self._raise_as_http(exc)

    @route(
        "/{public_id}/disable",
        methods=["PATCH"],
        response_model=UserRead,
        summary="禁用用户",
        description="将指定用户标记为禁用状态。",
    )
    async def disable_user(self, public_id: str, session: SessionDep) -> UserRead:
        """禁用用户。

        Args:
            public_id: 对外公开的用户标识。
            session: 当前数据库会话依赖。

        Returns:
            UserRead: 已更新为禁用状态的用户对象。
        """
        try:
            return await user_service.disable_user(session, public_id)
        except user_service.UserServiceError as exc:
            self._raise_as_http(exc)

    @route(
        "/{public_id}",
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
        summary="删除用户",
        description="根据用户公开 ID 删除对应的用户记录。",
    )
    async def delete_user(self, public_id: str, session: SessionDep) -> Response:
        """删除用户。

        Args:
            public_id: 对外公开的用户标识。
            session: 当前数据库会话依赖。

        Returns:
            Response: 空响应体的 204 删除结果。
        """
        try:
            await user_service.delete_user(session, public_id)
        except user_service.UserServiceError as exc:
            self._raise_as_http(exc)
        return Response(status_code=status.HTTP_204_NO_CONTENT)


router = UserView()()
