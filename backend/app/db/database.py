from __future__ import annotations

import asyncpg


class Database:
    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise RuntimeError("DATABASE_URL не задан")
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=1,
            max_size=10,
            command_timeout=30,
        )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Пул соединений не инициализирован")
        return self._pool