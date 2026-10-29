import os
from pathlib import Path
from cryptography.fernet import Fernet
from loguru import logger
from app.core.config import settings

# Путь к мастер-ключу (остается в data/secret)
MASTER_KEY_FILE = Path(settings.data_dir).resolve() / "secret" / "master.key"

def get_master_key() -> bytes:
    if MASTER_KEY_FILE.exists():
        return MASTER_KEY_FILE.read_bytes()
    
    key = Fernet.generate_key()
    MASTER_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MASTER_KEY_FILE.write_bytes(key)
    MASTER_KEY_FILE.chmod(0o600)
    
    logger.warning(f"Сгенерирован новый мастер-ключ: {MASTER_KEY_FILE}")
    return key

try:
    _fernet = Fernet(get_master_key())
except Exception as e:
    logger.error(f"Ошибка инициализации Fernet: {e}")
    _fernet = None

def encrypt_secret(value: str) -> str:
    if not value or not _fernet:
        return value
    return _fernet.encrypt(value.encode()).decode()

def decrypt_secret(encrypted_value: str) -> str:
    if not encrypted_value or not _fernet:
        return encrypted_value
    try:
        return _fernet.decrypt(encrypted_value.encode()).decode()
    except Exception:
        return encrypted_value