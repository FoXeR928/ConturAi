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
            "SELECT id, login, password_hash, display_name, role, is_active "
            "FROM users WHERE id = $1",
            uid,
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

    async def list_all(self) -> list[dict[str, Any]]:
        rows = await self._pool.fetch(
            "SELECT id, login, display_name, role, is_active "
            "FROM users ORDER BY created_at ASC"
        )
        return [
            {
                "id": str(r["id"]),
                "login": r["login"],
                "display_name": r["display_name"],
                "role": r["role"],
                "is_active": r["is_active"],
            }
            for r in rows
        ]

    async def count(self) -> int:
        return int(await self._pool.fetchval("SELECT COUNT(*) FROM users"))

    async def count_active_admins(self) -> int:
        return int(await self._pool.fetchval(
            "SELECT COUNT(*) FROM users "
            "WHERE role = 'admin' AND is_active = TRUE"
        ))

    async def update_role(self, user_id: str, role: str) -> None:
        await self._pool.execute(
            "UPDATE users SET role = $1 WHERE id = $2",
            role, uuid.UUID(user_id),
        )

    async def update_active(self, user_id: str, is_active: bool) -> None:
        await self._pool.execute(
            "UPDATE users SET is_active = $1 WHERE id = $2",
            is_active, uuid.UUID(user_id),
        )

    async def update_password(self, user_id: str, password_hash: str) -> None:
        await self._pool.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2",
            password_hash, uuid.UUID(user_id),
        )

    async def update_display_name(self, user_id: str, name: str) -> None:
        await self._pool.execute(
            "UPDATE users SET display_name = $1 WHERE id = $2",
            name, uuid.UUID(user_id),
        )

    async def delete(self, user_id: str) -> None:
        await self._pool.execute(
            "DELETE FROM users WHERE id = $1", uuid.UUID(user_id),
        )