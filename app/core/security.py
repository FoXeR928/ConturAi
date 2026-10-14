from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt

from app.core.config import settings
from app.core.secrets_store import load_or_create_jwt_key


@lru_cache(maxsize=1)
def _jwt_key() -> str:
    return load_or_create_jwt_key()


def create_access_token(login: str, long_lived: bool = False) -> str:
    delta = (
        timedelta(days=settings.token_expire_days)
        if long_lived
        else timedelta(minutes=settings.token_expire_minutes)
    )
    payload = {"sub": login, "exp": datetime.now(timezone.utc) + delta}
    return jwt.encode(payload, _jwt_key(), algorithm="HS256")


def decode_token(token: str) -> str:
    payload = jwt.decode(token, _jwt_key(), algorithms=["HS256"])
    return payload["sub"]