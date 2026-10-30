from __future__ import annotations

import json
from typing import Any, AsyncGenerator

import httpx

from app.plugins.base import BasePlugin
from app.schemas.plugin import (
    ChatMessage,
    PipelineContext,
    PluginManifest,
)


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

    def _payload(self, ctx: PipelineContext) -> dict[str, Any]:
        return {
            "prompt": ctx.prompt,
            "history": [m.model_dump() for m in ctx.history],
            "attachments": ctx.attachments,
            "metadata": ctx.metadata,
            "answer": ctx.answer,
            "settings": self.settings,
        }

    def _apply_response(self, ctx: PipelineContext, data: dict[str, Any]) -> PipelineContext:
        if isinstance(data.get("prompt"), str):
            ctx.prompt = data["prompt"]
        if isinstance(data.get("history"), list):
            ctx.history = [ChatMessage(**m) for m in data["history"]]
        if isinstance(data.get("metadata"), dict):
            ctx.metadata.update(data["metadata"])
        if isinstance(data.get("attachments"), list):
            ctx.attachments = data["attachments"]
        if isinstance(data.get("answer"), str):
            ctx.answer = data["answer"]
        return ctx

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        response = await self._client.post(
            f"{self.endpoint_url}/execute",
            json=self._payload(ctx),
            timeout=float(self.manifest.execution_timeout),
        )
        response.raise_for_status()
        return self._apply_response(ctx, response.json())

    async def execute_stream(
        self, ctx: PipelineContext,
    ) -> AsyncGenerator[str, None]:
        async with self._client.stream(
            "POST",
            f"{self.endpoint_url}/execute/stream",
            json=self._payload(ctx),
            timeout=None,
        ) as response:
            if response.status_code == 404:
                ctx = await self.execute(ctx)
                if ctx.answer:
                    yield ctx.answer
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
                    ctx.answer = (ctx.answer or "") + delta
                    yield delta

    async def check_health(self) -> bool:
        try:
            response = await self._client.post(
                f"{self.endpoint_url}/health", timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    async def shutdown(self) -> None:
        return None