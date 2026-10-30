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
    cors_origins: tuple[str, ...]
    login_rate_limit: int
    login_window_seconds: int
    message_rate_limit: int
    message_window_seconds: int
    external_plugin_health_interval: int

    @classmethod
    def load(cls) -> "Settings":
        cors_raw = os.getenv("CORS_ORIGINS", "").strip()
        cors = tuple(
            origin.strip()
            for origin in cors_raw.split(",")
            if origin.strip()
        )
        return cls(
            database_url=os.getenv("DATABASE_URL", ""),
            jwt_secret=os.getenv("JWT_SECRET", "change-me"),
            jwt_algorithm="HS256",
            jwt_expire_minutes=60 * 24 * 7,
            admin_password=os.getenv("ADMIN_PASSWORD") or None,
            cors_origins=cors,
            login_rate_limit=5,
            login_window_seconds=300,
            message_rate_limit=30,
            message_window_seconds=300,
            external_plugin_health_interval=30,
        )


settings = Settings.load()