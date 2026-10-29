from __future__ import annotations

import uuid
from typing import Any

import asyncpg


class UserStore:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(
        self,
        login: str,
        password_hash: str,
        display_name: str | None = None,
        role: str = "user",
    ) -> str:
        row = await self._pool.fetchrow(
            """
            INSERT INTO users (login, password_hash, display_name, role)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            login, password_hash, display_name, role,
        )
        return str(row["id"])

    async def get_by_login(self, login: str) -> dict[str, Any] | None:
        row = await self._pool.fetchrow(
            "SELECT id, login, password_hash, display_name, role, is_active "
            "FROM users WHERE login = $1",
            login,
        )
        if row is None:
            return None
        return {
            "id": str(row["id"]),
            "login": row["login"],
            "password_hash": row["password_hash"],
            "display_name": row["display_name"],
            "role": row["role"],
            "is_active": row["is_active"],
        }

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return None
        row = await self._pool.fetchrow(
            "SELECT id, login, display_name, role, is_active "
            "FROM users WHERE id = $1",
            uid,
        )
        if row is None:
            return None
        return {
            "id": str(row["id"]),
            "login": row["login"],
            "display_name": row["display_name"],
            "role": row["role"],
            "is_active": row["is_active"],
        }

    async def count(self) -> int:
        return int(await self._pool.fetchval("SELECT COUNT(*) FROM users"))