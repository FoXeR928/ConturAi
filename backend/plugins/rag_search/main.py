from __future__ import annotations

from typing import Any

import asyncpg

from app.plugins.context import PluginSystemContext
from app.schemas.plugin import PipelineContext


_pool: asyncpg.Pool | None = None
_dsn: str = ""


def configure(ctx: PluginSystemContext) -> None:
    global _dsn
    _dsn = ctx.database_url


async def _get_pool(settings: dict[str, Any]) -> asyncpg.Pool:
    global _pool, _dsn
    target_dsn = str(settings.get("database_url") or _dsn)
    if _pool is None:
        _pool = await asyncpg.create_pool(target_dsn, min_size=1, max_size=5)
    return _pool


async def _ensure_schema(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rag_chunks (
                id BIGSERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                tags TEXT[] DEFAULT '{}',
                source TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rag_tags ON rag_chunks USING GIN (tags)"
        )
        # seed однажды для демо
        count = await conn.fetchval("SELECT COUNT(*) FROM rag_chunks")
        if count == 0:
            await conn.execute(
                """
                INSERT INTO rag_chunks (content, tags, source) VALUES
                ($1, $2, $3),
                ($4, $5, $6),
                ($7, $8, $9)
                """,
                "ConturAI — модульная AI-платформа с плагинами",
                ["conturai", "архитектура"],
                "readme",
                "Плагины бывают internal (Python в ядре) и external (Docker по сети)",
                ["conturai", "плагины"],
                "readme",
                "PipelineContext передаётся по цепочке плагинов и обогащается ими",
                ["pipeline", "архитектура"],
                "readme",
            )


async def handle(
    ctx: PipelineContext, settings: dict[str, Any],
) -> PipelineContext:
    if not settings.get("enabled", True):
        return ctx

    top_k = int(settings.get("top_k", 5))
    tags_raw = str(settings.get("tags", "")).strip()
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

    pool = await _get_pool(settings)
    await _ensure_schema(pool)

    query = ctx.prompt
    async with pool.acquire() as conn:
        if tags:
            rows = await conn.fetch(
                """
                SELECT content, tags, source
                FROM rag_chunks
                WHERE tags && $1::text[]
                AND content ILIKE $2
                LIMIT $3
                """,
                tags, f"%{query[:100]}%", top_k,
            )
            if not rows:
                rows = await conn.fetch(
                    "SELECT content, tags, source FROM rag_chunks WHERE tags && $1::text[] LIMIT $2",
                    tags, top_k,
                )
        else:
            rows = await conn.fetch(
                """
                SELECT content, tags, source
                FROM rag_chunks
                WHERE content ILIKE $1
                LIMIT $2
                """,
                f"%{query[:100]}%", top_k,
            )
            if not rows:
                rows = await conn.fetch(
                    "SELECT content, tags, source FROM rag_chunks LIMIT $1",
                    top_k,
                )

    if not rows:
        return ctx

    docs = [
        {"content": r["content"], "tags": list(r["tags"] or []), "source": r["source"]}
        for r in rows
    ]
    ctx.metadata["rag_documents"] = docs
    ctx.metadata["rag_used"] = True

    rag_text = "\n".join(f"- {d['content']}" for d in docs)
    ctx.prompt = (
        f"Релевантные документы из базы знаний:\n{rag_text}\n\n"
        f"Вопрос пользователя: {ctx.prompt}"
    )
    return ctx


async def shutdown() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None