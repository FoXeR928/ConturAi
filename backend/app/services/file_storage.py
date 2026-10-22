import uuid
from pathlib import Path

from loguru import logger

from app.core.config import settings

UPLOADS_DIR = Path(settings.data_dir).resolve() / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def save_original(data: bytes, original_name: str) -> str:
    """Сохраняет оригинал на диск, возвращает stored_name для БД."""
    ext = Path(original_name).suffix.lower() or ".bin"
    stored = f"{uuid.uuid4().hex}{ext}"
    path = UPLOADS_DIR / stored
    path.write_bytes(data)
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