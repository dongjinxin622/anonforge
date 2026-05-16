import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from app.core.config import settings
from app.routers.api import api_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """在应用启动时完成一些初始化操作，例如：数据库连接，启动一些后台任务之类的。
    """
    # yield之前的代码，属于App创建之前执行[只需要在项目开始前执行一次的操作，初始化数据库等外部链接，]
    print("yield之前")
    yield
    # yield之后的代码，属于App关闭之后执行[记录并回收资源]
    print("yield之后")

def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。

    Returns:
        FastAPI: 已注册全局路由和生命周期钩子的应用对象。
    """
    app = FastAPI(
            title=settings.app_name,
            description=settings.app_description,
            lifespan=lifespan
    )

    app.include_router(api_router)

    return app

app = create_app()
