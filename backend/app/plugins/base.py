from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from app.schemas.plugin import PipelineContext, PluginManifest


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
    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """Основная логика плагина. Модифицирует и возвращает ctx."""
        ...

    async def execute_stream(
        self, ctx: PipelineContext,
    ) -> AsyncGenerator[str, None]:
        """Стриминговая версия. По умолчанию — вызывает execute и отдаёт одним чанком."""
        ctx = await self.execute(ctx)
        if ctx.answer:
            yield ctx.answer

    async def reconfigure(self) -> None:
        """Вызывается после update_settings. Плагин решает, что делать
        (например, пересоздать контейнер vLLM)."""
        return None

    async def check_health(self) -> bool:
        return True

    async def shutdown(self) -> None:
        return None