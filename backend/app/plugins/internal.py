from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.plugins.base import BasePlugin
from app.plugins.context import PluginContext
from app.schemas.plugin import ChatMessage, PluginManifest


Handler = Callable[[str, list[ChatMessage], dict[str, Any]], Awaitable[str]]


class InternalPlugin(BasePlugin):
    def __init__(
        self,
        manifest: PluginManifest,
        settings: dict[str, Any],
        entry_path: Path,
        context: PluginContext,
    ) -> None:
        super().__init__(manifest, settings)
        self._entry_path = entry_path
        self._context = context
        self._handler: Handler | None = None

    async def setup(self) -> None:
        if self._handler is not None:
            return

        module_name = f"conturai_plugin_{self.manifest.id}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(
            module_name, self._entry_path,
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(
                f"Не удалось создать spec для {self._entry_path}",
            )

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        configure = getattr(module, "configure", None)
        if configure is not None and callable(configure):
            result = configure(self._context)
            if inspect.isawaitable(result):
                await result

        handler = getattr(module, "handle", None)
        if handler is None or not callable(handler):
            raise RuntimeError(
                f"Плагин {self.manifest.id}: отсутствует "
                f"async def handle(prompt, history, settings)",
            )
        self._handler = handler

    async def execute(self, prompt: str, history: list[ChatMessage]) -> str:
        await self.setup()
        assert self._handler is not None
        result = await self._handler(prompt, history, self.settings)
        if not isinstance(result, str):
            raise RuntimeError(
                f"Плагин {self.manifest.id}: handle() должен вернуть str",
            )
        return result