"""
LLM-провайдер для vLLM через OpenAI-совместимый API.

PLUGIN_URL выставляет ядро при загрузке (см. app/kernel/loader.py).
Фиксируем его на уровне модуля — до того, как loader восстановит env.
"""

import os
from typing import AsyncGenerator

from loguru import logger
from openai import AsyncOpenAI

from app.kernel import kernel
from app.kernel.contracts import BaseLLMProvider

_PLUGIN_URL = os.environ.get("PLUGIN_URL") or os.environ.get("PLUGIN_LLM_VLLM_URL")
if not _PLUGIN_URL:
    raise RuntimeError("PLUGIN_URL не установлен ядром — плагин не может стартовать")

_MODEL_NAME = os.environ.get("VLLM_MODEL_NAME", "local-model")


class VLLMProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url=f"{_PLUGIN_URL}/v1",
            api_key="EMPTY",  # vLLM не проверяет
        )
        self._model = _MODEL_NAME
        logger.info(f"[llm_vllm] init: url={_PLUGIN_URL}, model={self._model}")

    async def generate(self, messages: list[dict], **kwargs) -> str:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=float(kwargs.get("temperature", 0.7)),
            max_tokens=int(kwargs.get("max_tokens", 1024)),
        )
        return resp.choices[0].message.content or ""

    async def generate_stream(
        self, messages: list[dict], **kwargs
    ) -> AsyncGenerator[str, None]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=float(kwargs.get("temperature", 0.7)),
            max_tokens=int(kwargs.get("max_tokens", 1024)),
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def check_health(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception as e:
            logger.warning(f"[llm_vllm] health: {e}")
            return False


kernel.llm_provider(VLLMProvider)