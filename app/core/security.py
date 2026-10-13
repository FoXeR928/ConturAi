from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def create_access_token(login: str, long_lived: bool = False) -> str:
    delta = (
        timedelta(days=settings.token_expire_days)
        if long_lived
        else timedelta(minutes=settings.token_expire_minutes)
    )
    payload = {"sub": login, "exp": datetime.now(timezone.utc) + delta}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> str:
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    return payload["sub"]