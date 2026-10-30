from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, AsyncGenerator

from app.plugins.base import BasePlugin
from app.plugins.context import PluginSystemContext
from app.schemas.plugin import PipelineContext, PluginManifest


class InternalPlugin(BasePlugin):
    def __init__(
        self,
        manifest: PluginManifest,
        settings: dict[str, Any],
        entry_path: Path,
        sys_ctx: PluginSystemContext,
    ) -> None:
        super().__init__(manifest, settings)
        self._entry_path = entry_path
        self._sys_ctx = sys_ctx
        self._module: Any = None
        self._handle = None
        self._handle_stream = None
        self._handle_reconfigure = None
        self._handle_shutdown = None
        self._handle_health = None

    async def _ensure_loaded(self) -> None:
        if self._module is not None:
            return

        module_name = f"conturai_plugin_{self.manifest.id}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(
            module_name, self._entry_path,
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"spec creation failed: {self._entry_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        self._module = module

        configure = getattr(module, "configure", None)
        if callable(configure):
            result = configure(self._sys_ctx)
            if inspect.isawaitable(result):
                await result

        handle = getattr(module, "handle", None)
        if not callable(handle):
            raise RuntimeError(
                f"Плагин {self.manifest.id}: отсутствует async def handle(ctx, settings)"
            )
        self._handle = handle

        stream = getattr(module, "handle_stream", None)
        if callable(stream):
            self._handle_stream = stream

        reconfigure = getattr(module, "reconfigure", None)
        if callable(reconfigure):
            self._handle_reconfigure = reconfigure

        shutdown = getattr(module, "shutdown", None)
        if callable(shutdown):
            self._handle_shutdown = shutdown

        health = getattr(module, "check_health", None)
        if callable(health):
            self._handle_health = health

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        await self._ensure_loaded()
        assert self._handle is not None
        result = await self._handle(ctx, self.settings)
        if not isinstance(result, PipelineContext):
            raise RuntimeError(
                f"Плагин {self.manifest.id}: handle() должен вернуть PipelineContext"
            )
        return result

    async def execute_stream(
        self, ctx: PipelineContext,
    ) -> AsyncGenerator[str, None]:
        await self._ensure_loaded()
        if self._handle_stream is None:
            ctx = await self.execute(ctx)
            if ctx.answer:
                yield ctx.answer
            return
        async for chunk in self._handle_stream(ctx, self.settings):
            if isinstance(chunk, str):
                ctx.answer = (ctx.answer or "") + chunk
                yield chunk

    async def reconfigure(self) -> None:
        await self._ensure_loaded()
        if self._handle_reconfigure is not None:
            await self._handle_reconfigure(self.settings)

    async def check_health(self) -> bool:
        await self._ensure_loaded()
        if self._handle_health is None:
            return True
        try:
            return bool(await self._handle_health(self.settings))
        except Exception:
            return False

    async def shutdown(self) -> None:
        if self._handle_shutdown is not None:
            try:
                await self._handle_shutdown()
            except Exception:
                pass