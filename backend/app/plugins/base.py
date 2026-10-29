from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.plugin import ChatMessage, PluginManifest


class BasePlugin(ABC):
    def __init__(
        self, manifest: PluginManifest, settings: dict[str, Any],
    ) -> None:
        self.manifest = manifest
        self.settings = settings

    def get_manifest(self) -> PluginManifest:
        return self.manifest

    def update_settings(self, settings: dict[str, Any]) -> None:
        self.settings = settings

    @abstractmethod
    async def execute(self, prompt: str, history: list[ChatMessage]) -> str:
        ...