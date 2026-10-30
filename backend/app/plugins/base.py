from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from app.schemas.plugin import ChatMessage, PluginManifest


class BasePlugin(ABC):
    def __init__(self, manifest: PluginManifest, settings: dict[str, Any]) -> None:
        self.manifest = manifest
        self.settings = settings
        self.health_status: str = "unknown"

    def get_manifest(self) -> PluginManifest:
        return self.manifest

    def update_settings(self, settings: dict[str, Any]) -> None:
        self.settings = settings

    @abstractmethod
    async def execute(self, prompt: str, history: list[ChatMessage]) -> str:
        ...

    async def execute_stream(
        self, prompt: str, history: list[ChatMessage],
    ) -> AsyncGenerator[str, None]:
        """По умолчанию — фоллбэк на execute() одним чанком."""
        yield await self.execute(prompt, history)

    async def check_health(self) -> bool:
        return True

    async def shutdown(self) -> None:
        """Опционально: освобождение ресурсов при остановке ядра."""
        return None