import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.routers.api import api_router
from app.services.user import ensure_default_admin


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用生命周期钩子。

    启动时创建数据库表，并确保系统中存在默认管理员用户。
    """
    await ensure_default_admin()
    yield


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。

    Returns:
        FastAPI: 已注册全局路由和生命周期钩子的应用对象。
    """
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        lifespan=lifespan,
    )

    app.include_router(api_router)

    return app


app = create_app()
