from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.string_tools import hash_password
from app.utils.time_tools import utc_now


class UserServiceError(Exception):
    """用户服务层基础异常。"""


class UserNotFoundError(UserServiceError):
    """用户不存在异常。"""


class UserNameConflictError(UserServiceError):
    """用户名冲突异常。"""


class UserEmailConflictError(UserServiceError):
    """用户邮箱冲突异常。"""


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    """按用户名查询单个用户。"""
    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    return result.first()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """按邮箱查询单个用户。"""
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    return result.first()


async def get_user_by_public_id(session: AsyncSession, public_id: str) -> User | None:
    """按公开 ID 查询单个用户。"""
    statement = select(User).where(User.public_id == public_id)
    result = await session.exec(statement)
    return result.first()


async def get_user_or_raise(session: AsyncSession, public_id: str) -> User:
    """按公开 ID 获取用户，不存在时抛出业务异常。"""
    user = await get_user_by_public_id(session, public_id)
    if user is None:
        raise UserNotFoundError("User not found")
    return user


async def ensure_unique_username(
    session: AsyncSession,
    username: str,
    current_user_id: int | None = None,
) -> None:
    """校验用户名在当前系统内唯一。"""
    existing_user = await get_user_by_username(session, username)
    if existing_user is None:
        return
    if current_user_id is not None and existing_user.id == current_user_id:
        return
    raise UserNameConflictError("Username already exists")


async def ensure_unique_email(
    session: AsyncSession,
    email: str | None,
    current_user_id: int | None = None,
) -> None:
    """校验非空邮箱在当前系统内唯一。"""
    if email is None:
        return

    existing_user = await get_user_by_email(session, email)
    if existing_user is None:
        return
    if current_user_id is not None and existing_user.id == current_user_id:
        return
    raise UserEmailConflictError("Email already exists")


async def list_users(session: AsyncSession) -> list[User]:
    """获取用户列表。"""
    statement = select(User).order_by(User.sort_order, User.id)
    result = await session.exec(statement)
    return list(result.all())


async def create_user(session: AsyncSession, payload: UserCreate) -> User:
    """创建用户。"""
    await ensure_unique_username(session, payload.username)
    await ensure_unique_email(session, payload.email)

    now = utc_now()
    user = User(
        username=payload.username,
        nickname=payload.nickname,
        email=payload.email,
        avatar_url=payload.avatar_url,
        password_hash=hash_password(payload.password),
        sort_order=payload.sort_order,
        is_superuser=payload.is_superuser,
        disabled_at=None,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(session: AsyncSession, public_id: str, payload: UserUpdate) -> User:
    """更新用户信息。"""
    user = await get_user_or_raise(session, public_id)
    fields_set = payload.model_fields_set

    if "username" in fields_set and payload.username is not None:
        await ensure_unique_username(session, payload.username, current_user_id=user.id)
        user.username = payload.username
    if "email" in fields_set:
        await ensure_unique_email(session, payload.email, current_user_id=user.id)
        user.email = payload.email
    if "nickname" in fields_set:
        user.nickname = payload.nickname
    if "avatar_url" in fields_set:
        user.avatar_url = payload.avatar_url
    if "password" in fields_set and payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if "sort_order" in fields_set and payload.sort_order is not None:
        user.sort_order = payload.sort_order
    if "is_superuser" in fields_set and payload.is_superuser is not None:
        user.is_superuser = payload.is_superuser
    if "disabled_at" in fields_set:
        user.disabled_at = payload.disabled_at

    user.updated_at = utc_now()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def disable_user(session: AsyncSession, public_id: str) -> User:
    """禁用用户。"""
    user = await get_user_or_raise(session, public_id)
    await user.disable()
    user.updated_at = utc_now()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, public_id: str) -> None:
    """删除用户。"""
    user = await get_user_or_raise(session, public_id)
    await session.delete(user)
    await session.commit()


async def ensure_default_admin() -> None:
    """确保数据库中存在默认管理员账号。"""
    async with async_session_maker() as session:
        result = await session.exec(select(User.id).where(User.is_superuser.is_(True)))
        existing_admin = result.first()
        if existing_admin is not None:
            return

        admin_user = await get_user_by_username(session, settings.user_default_admin_name)
        if admin_user is not None:
            admin_user.is_superuser = True
            admin_user.updated_at = utc_now()
            session.add(admin_user)
            await session.commit()
            return

        now = utc_now()
        admin_user = User(
            username=settings.user_default_admin_name,
            nickname=settings.user_default_admin_name,
            password_hash=hash_password(settings.user_default_admin_password),
            sort_order=0,
            is_superuser=True,
            disabled_at=None,
            created_at=now,
            updated_at=now,
        )
        session.add(admin_user)
        await session.commit()
