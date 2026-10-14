import secrets

from loguru import logger

from app.core.paths import JWT_KEY_FILE


def load_or_create_jwt_key() -> str:
    if JWT_KEY_FILE.exists():
        key = JWT_KEY_FILE.read_text(encoding="utf-8").strip()
        if key:
            return key

    key = secrets.token_urlsafe(64)
    JWT_KEY_FILE.write_text(key, encoding="utf-8")
    JWT_KEY_FILE.chmod(0o600)
    logger.warning(f"Сгенерирован новый JWT-ключ: {JWT_KEY_FILE}")
    return key