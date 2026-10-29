from __future__ import annotations

from typing import Any

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
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        result = data.get("response")
        if not isinstance(result, str):
            raise RuntimeError(
                f"Плагин {self.manifest.id}: ответ должен содержать "
                f"строковое поле 'response'",
            )
        return result