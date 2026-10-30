from __future__ import annotations

import uuid
from typing import Any

import asyncpg

from app.plugins.context import PluginSystemContext
from app.schemas.plugin import ChatMessage, PipelineContext


_pool: asyncpg.Pool | None = None


def configure(ctx: PluginSystemContext) -> None:
    global _pool
    if _pool is None and ctx.database_url:
        _pool = None  # создадим лениво
        globals()["_dsn"] = ctx.database_url


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        dsn = globals().get("_dsn")
        if not dsn:
            raise RuntimeError("database_url не передан в configure()")
        _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
    return _pool


async def handle(
    ctx: PipelineContext, settings: dict[str, Any],
) -> PipelineContext:
    chat_id = ctx.metadata.get("chat_id")
    if not chat_id:
        return ctx

    try:
        chat_uuid = uuid.UUID(str(chat_id))
    except ValueError:
        return ctx

    max_messages = int(settings.get("max_messages", 20))
    max_chars = int(settings.get("max_chars", 8000))

    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT role, content FROM messages
            WHERE chat_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            chat_uuid, max_messages,
        )

    history: list[ChatMessage] = []
    total = 0
    for row in reversed(rows):
        role = row["role"]
        if role not in ("user", "assistant", "system"):
            continue
        content = row["content"]
        if total + len(content) > max_chars:
            break
        history.append(ChatMessage(role=role, content=content))
        total += len(content)

    ctx.history = history
    ctx.metadata["context_loaded"] = len(history)
    return ctx


async def shutdown() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None