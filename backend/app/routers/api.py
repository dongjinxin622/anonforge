from fastapi import APIRouter

from app.core.config import settings
from app.routers.project import router as project_router
from app.routers.user import router as user_router

api_router = APIRouter(prefix=settings.api_prefix)

api_router.include_router(project_router)
api_router.include_router(user_router)

@api_router.get(
    "/health",  # 实际路径：/api/health
    summary="健康检查",
    description="检查后端服务是否正常运行。",
)
async def health_check() -> dict[str, str]:
    """返回服务健康状态。
    Returns:
        dict[str, str]: 固定返回 `status=ok` 的状态对象。
    """
    return {"status": "ok"}