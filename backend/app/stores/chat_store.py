from __future__ import annotations

import uuid
from typing import Any

import asyncpg


class ChatStore:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, user_id: str, title: str) -> str:
        row = await self._pool.fetchrow(
            "INSERT INTO chats (user_id, title) VALUES ($1, $2) RETURNING id",
            uuid.UUID(user_id), title,
        )
        return str(row["id"])

    async def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        rows = await self._pool.fetch(
            "SELECT id, title, created_at FROM chats "
            "WHERE user_id = $1 ORDER BY created_at DESC",
            uuid.UUID(user_id),
        )
        return [
            {
                "id": str(r["id"]),
                "title": r["title"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ]

    async def get(self, chat_id: str, user_id: str) -> dict[str, Any] | None:
        try:
            cid, uid = uuid.UUID(chat_id), uuid.UUID(user_id)
        except ValueError:
            return None
        row = await self._pool.fetchrow(
            "SELECT id, title FROM chats WHERE id = $1 AND user_id = $2",
            cid, uid,
        )
        if row is None:
            return None
        return {"id": str(row["id"]), "title": row["title"]}

    async def delete(self, chat_id: str, user_id: str) -> bool:
        try:
            cid, uid = uuid.UUID(chat_id), uuid.UUID(user_id)
        except ValueError:
            return False
        result = await self._pool.execute(
            "DELETE FROM chats WHERE id = $1 AND user_id = $2", cid, uid,
        )
        return result.endswith("1")

    async def add_message(self, chat_id: str, role: str, content: str) -> int:
        message_id = await self._pool.fetchval(
            "INSERT INTO messages (chat_id, role, content) VALUES ($1, $2, $3) "
            "RETURNING id",
            uuid.UUID(chat_id), role, content,
        )
        await self._pool.execute(
            "UPDATE chats SET updated_at = NOW() WHERE id = $1",
            uuid.UUID(chat_id),
        )
        return int(message_id)

    async def list_messages(
        self, chat_id: str, limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = await self._pool.fetch(
            "SELECT id, role, content, created_at FROM messages "
            "WHERE chat_id = $1 ORDER BY created_at ASC, id ASC LIMIT $2",
            uuid.UUID(chat_id), limit,
        )
        return [
            {
                "id": int(r["id"]),
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ]