import sys
import asyncio

# fastAPI+uvicorn在windows系统下异步运行时，会经常出现端口冲突，修改事件循环机制可以解决。
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import create_db_and_tables, engine
from app.routers.api import api_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用生命周期管理：启动时初始化数据库连接与表结构，关闭时释放引擎资源。"""
    await create_db_and_tables()
    yield
    await engine.dispose()


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