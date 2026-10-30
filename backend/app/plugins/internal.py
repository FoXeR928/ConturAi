from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, AsyncGenerator, Awaitable, Callable

from app.plugins.base import BasePlugin
from app.plugins.context import PluginContext
from app.schemas.plugin import ChatMessage, PluginManifest


Handler = Callable[[str, list[ChatMessage], dict[str, Any]], Awaitable[str]]
StreamHandler = Callable[
    [str, list[ChatMessage], dict[str, Any]],
    AsyncGenerator[str, None],
]
ShutdownHandler = Callable[[], Awaitable[None]]


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
        self._stream_handler: StreamHandler | None = None
        self._shutdown_handler: ShutdownHandler | None = None
        self._module: Any = None

    async def setup(self) -> None:
        if self._handler is not None:
            return

        module_name = f"conturai_plugin_{self.manifest.id}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(module_name, self._entry_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Не удалось создать spec для {self._entry_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        self._module = module

        configure = getattr(module, "configure", None)
        if configure is not None and callable(configure):
            result = configure(self._context)
            if inspect.isawaitable(result):
                await result

        handler = getattr(module, "handle", None)
        if handler is None or not callable(handler):
            raise RuntimeError(
                f"Плагин {self.manifest.id}: отсутствует async def handle()"
            )
        self._handler = handler

        stream = getattr(module, "handle_stream", None)
        if stream is not None and callable(stream):
            self._stream_handler = stream
            self.manifest = self.manifest.model_copy(update={"streaming": True})

        shutdown = getattr(module, "shutdown", None)
        if shutdown is not None and callable(shutdown):
            self._shutdown_handler = shutdown

    async def execute(self, prompt: str, history: list[ChatMessage]) -> str:
        await self.setup()
        assert self._handler is not None
        result = await self._handler(prompt, history, self.settings)
        if not isinstance(result, str):
            raise RuntimeError(
                f"Плагин {self.manifest.id}: handle() должен вернуть str"
            )
        return result

    async def execute_stream(
        self, prompt: str, history: list[ChatMessage],
    ) -> AsyncGenerator[str, None]:
        await self.setup()
        if self._stream_handler is None:
            yield await self.execute(prompt, history)
            return
        async for chunk in self._stream_handler(prompt, history, self.settings):
            if isinstance(chunk, str):
                yield chunk

    async def shutdown(self) -> None:
        if self._shutdown_handler is not None:
            try:
                await self._shutdown_handler()
            except Exception:
                pass