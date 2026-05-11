from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings
from app.utils.string_tools import build_database_url


def build_engine():
    """构建异步数据库引擎。

    Returns:
        AsyncEngine: 基于当前配置创建的 SQLAlchemy 异步引擎实例。
    """
    database_url = build_database_url(
        db_engine=settings.db_engine,
        db_driver=settings.db_driver,
        db_host=settings.db_host,
        db_port=settings.db_port,
        db_name=settings.db_name,
        db_user=settings.db_user,
        db_password=settings.db_password,
    )
    return create_async_engine(database_url, echo=False)


engine = build_engine()


async def create_db_and_tables() -> None:
    """根据当前 SQLModel 元数据创建数据库表（异步）。"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_db_and_tables() -> None:
    """根据当前 SQLModel 元数据删除数据库表（异步）。"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """提供异步数据库会话依赖。

    Yields:
        AsyncSession: 当前请求可复用的 SQLModel 异步会话对象。
    """
    async with AsyncSession(engine) as session:
        yield session