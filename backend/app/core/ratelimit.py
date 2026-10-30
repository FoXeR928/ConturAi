from __future__ import annotations

import time
from collections import defaultdict

from app.core.errors import ApiError


class RateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, list[float]] = defaultdict(list)

    def hit(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        events = [t for t in self._events[key] if t > cutoff]
        if len(events) >= limit:
            raise ApiError(
                "RATE_LIMITED",
                f"Слишком много запросов, попробуйте через "
                f"{window_seconds} секунд",
                status=429,
            )
        events.append(now)
        self._events[key] = events


limiter = RateLimiter()