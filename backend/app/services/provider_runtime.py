from __future__ import annotations

import importlib
import inspect
import sys
from typing import Any

import httpx

from app.core.base_provider import BaseProvider
from app.services import provider as provider_service


class ProviderRuntimeError(provider_service.ProviderServiceError):
    """运行时加载或调度 provider 失败。"""


def create_provider(
    provider_key: str,
    model_type: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    input_values: dict[str, str] | None = None,
    timeout: float = 60.0,
    client: httpx.AsyncClient | None = None,
) -> BaseProvider:
    """按厂商 key 与模型类型创建运行时工具类实例。"""
    provider_class = get_provider_class(provider_key, model_type)
    return provider_class(
        api_key=api_key,
        base_url=base_url,
        input_values=input_values,
        timeout=timeout,
        client=client,
    )


def create_provider_for_model(
    model_id: str,
    *,
    provider_key: str | None = None,
    input_values: dict[str, str] | None = None,
    timeout: float = 60.0,
    client: httpx.AsyncClient | None = None,
) -> BaseProvider:
    """根据 model_id 查找配置中的模型能力，并创建对应 provider。"""
    model_id = model_id.strip()
    if not model_id:
        raise ProviderRuntimeError("model_id 不能为空")

    configs = (
        [provider_service.get_provider_config(provider_key)]
        if provider_key
        else provider_service.list_provider_configs()
    )
    for config in configs:
        if not config.enabled:
            continue
        for model in config.models:
            if model.model_id == model_id:
                return create_provider(
                    config.key,
                    model.model_type,
                    input_values=input_values,
                    timeout=timeout,
                    client=client,
                )
    raise ProviderRuntimeError("未找到可用的模型配置")


async def generate(
    provider_key: str,
    model_type: str,
    *,
    model_id: str | None = None,
    input_values: dict[str, str] | None = None,
    timeout: float = 60.0,
    client: httpx.AsyncClient | None = None,
    **kwargs: Any,
) -> Any:
    """统一调度 provider 工具类执行生成任务。"""
    provider = create_provider(
        provider_key,
        model_type,
        input_values=input_values,
        timeout=timeout,
        client=client,
    )
    return await provider.generate(model_id=model_id, **kwargs)


def get_provider_class(provider_key: str, model_type: str) -> type[BaseProvider]:
    config = provider_service.get_provider_config(provider_key)
    if not config.enabled:
        raise ProviderRuntimeError("服务未启用")

    module = load_provider_module(provider_key)
    matches: list[type[BaseProvider]] = []
    for value in vars(module).values():
        if not inspect.isclass(value) or value is BaseProvider:
            continue
        if not issubclass(value, BaseProvider):
            continue
        class_key = getattr(value, "provider_key", "")
        class_model_type = getattr(value, "model_type", "")
        if class_key == provider_key and class_model_type == model_type:
            matches.append(value)

    if not matches:
        raise ProviderRuntimeError("未找到匹配的 provider 工具类")
    if len(matches) > 1:
        raise ProviderRuntimeError("找到多个匹配的 provider 工具类")
    return matches[0]


def load_provider_module(provider_key: str):
    provider_service.get_provider_config(provider_key)
    module_name = f"app.providers.{provider_key}"
    try:
        if module_name in sys.modules:
            return importlib.reload(sys.modules[module_name])
        return importlib.import_module(module_name)
    except Exception as exc:
        raise ProviderRuntimeError(f"加载 provider 模块失败: {exc}") from exc