from __future__ import annotations

from typing import Any

from app.services import provider_runtime


class ProviderModelGatewayError(Exception):
    """模型网关调用失败。"""


class ProviderModelGateway:
    """按模型 ID 调用文本/图像/语音/视频 生成的 Provider。"""

    def __init__(self, *, timeout: float = 60.0) -> None:
        self.timeout = timeout

    async def generate_text(
        self,
        *,
        model_id: str,
        messages: list[dict[str, str]],
        provider_key: str | None = None,
        input_values: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            provider = provider_runtime.create_provider_for_model(
                model_id,
                provider_key=provider_key,
                input_values=input_values,
                timeout=self.timeout,
            )
            raw_output = await provider.generate(model_id=model_id, messages=messages, **kwargs)
            return self._extract_text(raw_output)
        except ProviderModelGatewayError:
            raise
        except Exception as exc:
            raise ProviderModelGatewayError(str(exc)) from exc

    def _extract_text(self, raw_output: Any) -> str:
        if isinstance(raw_output, str):
            return self._ensure_text(raw_output)

        if isinstance(raw_output, dict):
            for key in ("output_text", "text"):
                value = raw_output.get(key)
                if isinstance(value, str):
                    return self._ensure_text(value)

            choices = raw_output.get("choices")
            if isinstance(choices, list) and choices:
                choice = choices[0]
                if isinstance(choice, dict):
                    message = choice.get("message")
                    if isinstance(message, dict) and isinstance(message.get("content"), str):
                        return self._ensure_text(message["content"])
                    if isinstance(choice.get("text"), str):
                        return self._ensure_text(choice["text"])

        raise ProviderModelGatewayError("模型响应中没有可用文本")

    @staticmethod
    def _ensure_text(value: str) -> str:
        text = value.strip()
        if not text:
            raise ProviderModelGatewayError("模型响应文本为空")
        return text
