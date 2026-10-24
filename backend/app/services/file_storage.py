import uuid
from pathlib import Path

from loguru import logger

from app.core.config import settings

UPLOADS_DIR = Path(settings.data_dir).resolve() / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

logger.debug(f"UPLOADS_DIR = {UPLOADS_DIR}")
logger.debug(f"Writable: {__import__('os').access(UPLOADS_DIR, __import__('os').W_OK)}")


def save_original(data: bytes, original_name: str) -> str:
    ext = Path(original_name).suffix.lower() or ".bin"
    stored = f"{uuid.uuid4().hex}{ext}"
    path = UPLOADS_DIR / stored
    try:
        path.write_bytes(data)
    except Exception as err:
        logger.error(f"Не удалось сохранить файл {path}: {err}")
        raise
    logger.info(f"Оригинал сохранён: {path} ({len(data)} байт)")
    return stored


def path_of(stored_name: str) -> Path:
    return UPLOADS_DIR / stored_name


def delete_file(stored_name: str | None) -> None:
    if not stored_name:
        return
    path = UPLOADS_DIR / stored_name
    if path.exists():
        path.unlink()
        logger.info(f"Файл удалён: {path}")