from __future__ import annotations

import json
from typing import Any, AsyncGenerator

import httpx

from app.plugins.base import BasePlugin
from app.schemas.plugin import ChatMessage, PluginManifest


class ExternalPlugin(BasePlugin):
    def __init__(
        self,
        manifest: PluginManifest,
        settings: dict[str, Any],
        endpoint_url: str,
        client: httpx.AsyncClient,
    ) -> None:
        super().__init__(manifest, settings)
        self.endpoint_url = endpoint_url.rstrip("/")
        self._client = client

    async def execute(self, prompt: str, history: list[ChatMessage]) -> str:
        response = await self._client.post(
            f"{self.endpoint_url}/chat",
            json={
                "prompt": prompt,
                "history": [m.model_dump() for m in history],
                "settings": self.settings,
            },
            timeout=float(self.manifest.execution_timeout),
        )
        response.raise_for_status()
        data = response.json()
        result = data.get("response")
        if not isinstance(result, str):
            raise RuntimeError(
                f"Плагин {self.manifest.id}: ответ должен содержать 'response'"
            )
        return result

    async def execute_stream(
        self, prompt: str, history: list[ChatMessage],
    ) -> AsyncGenerator[str, None]:
        if not self.manifest.streaming:
            yield await self.execute(prompt, history)
            return

        payload = {
            "prompt": prompt,
            "history": [m.model_dump() for m in history],
            "settings": self.settings,
        }
        async with self._client.stream(
            "POST",
            f"{self.endpoint_url}/chat/stream",
            json=payload,
            timeout=None,
        ) as response:
            if response.status_code == 404:
                yield await self.execute(prompt, history)
                return
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                raw = line[6:]
                if raw == "[DONE]":
                    return
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                delta = obj.get("delta")
                if isinstance(delta, str) and delta:
                    yield delta

    async def check_health(self) -> bool:
        try:
            response = await self._client.post(
                f"{self.endpoint_url}/health", timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False