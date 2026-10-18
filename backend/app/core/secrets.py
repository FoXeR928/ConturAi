import os
import secrets as _secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import jwt
from loguru import logger

from app.core.config import settings

# ---------- Пути ----------
DATA_DIR = Path(os.getenv("CONTURAI_DATA_DIR", "/app/data"))
LOGS_DIR = DATA_DIR / "logs"
SECRET_DIR = DATA_DIR / "secret"
MODELS_DIR = Path(os.getenv("CONTURAI_MODELS_DIR", "/models"))

for _d in (DATA_DIR, LOGS_DIR, SECRET_DIR):
    _d.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / "app.log"
JWT_KEY_FILE = SECRET_DIR / "secret.jwt"


# ---------- JWT-ключ ----------
def load_or_create_jwt_key() -> str:
    if JWT_KEY_FILE.exists():
        key = JWT_KEY_FILE.read_text(encoding="utf-8").strip()
        if key:
            return key

    key = _secrets.token_urlsafe(64)
    JWT_KEY_FILE.write_text(key, encoding="utf-8")
    JWT_KEY_FILE.chmod(0o600)
    logger.warning(f"Сгенерирован новый JWT-ключ: {JWT_KEY_FILE}")
    return key


@lru_cache(maxsize=1)
def _jwt_key() -> str:
    return load_or_create_jwt_key()


# ---------- Токены ----------
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