from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["project"])


@router.get(
    "/",
    summary="项目模块占位接口",
    description="返回项目模块的基础占位信息，用于验证路由注册状态。",
)
async def list_projects() -> dict[str, str]:
    """获取项目模块占位信息。

    Returns:
        dict[str, str]: 当前模块的标识信息。
    """
    return {"module": "project"}
