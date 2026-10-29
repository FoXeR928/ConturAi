from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    admin_password: str | None

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            database_url=os.getenv("DATABASE_URL", ""),
            jwt_secret=os.getenv("JWT_SECRET", "change-me"),
            jwt_algorithm="HS256",
            jwt_expire_minutes=60 * 24 * 7,
            admin_password=os.getenv("ADMIN_PASSWORD") or None,
        )


settings = Settings.load()