from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator

from app.schemas.plugin import ChatMessage
from app.plugins.context import PluginContext


async def configure(context: PluginContext) -> None:
    _ = context


def _build(prompt: str, settings: dict[str, Any]) -> str:
    prefix = str(settings.get("prefix", ""))
    repeat = max(1, int(settings.get("repeat", 1)))
    style = str(settings.get("style", "plain"))
    text = f"{prefix}{prompt}"
    if style == "upper":
        text = text.upper()
    elif style == "lower":
        text = text.lower()
    return (text + " ") * repeat


async def handle(
    prompt: str,
    history: list[ChatMessage],
    settings: dict[str, Any],
) -> str:
    return _build(prompt, settings)


async def handle_stream(
    prompt: str,
    history: list[ChatMessage],
    settings: dict[str, Any],
) -> AsyncGenerator[str, None]:
    text = _build(prompt, settings)
    for word in text.split(" "):
        if word:
            yield word + " "
            await asyncio.sleep(0.05)