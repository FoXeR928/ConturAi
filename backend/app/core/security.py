import os
from pathlib import Path
from cryptography.fernet import Fernet
from loguru import logger

# Файл с мастер-ключом (не хранится в БД!)
MASTER_KEY_FILE = Path("./data/secret/master.key")

def get_master_key() -> bytes:
    """Читает или создает мастер-ключ для шифрования."""
    if MASTER_KEY_FILE.exists():
        return MASTER_KEY_FILE.read_bytes()
    
    # Создаем новый ключ
    key = Fernet.generate_key()
    MASTER_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MASTER_KEY_FILE.write_bytes(key)
    MASTER_KEY_FILE.chmod(0o600)  # Только владелец может читать
    logger.warning("Сгенерирован новый мастер-ключ шифрования.")
    return key

_fernet = Fernet(get_master_key())

def encrypt_secret(value: str) -> str:
    """Шифрует строку и возвращает в base64."""
    if not value:
        return value
    return _fernet.encrypt(value.encode()).decode()

def decrypt_secret(encrypted_value: str) -> str:
    """Расшифровывает строку. Если текст не зашифрован — возвращает как есть."""
    if not encrypted_value:
        return encrypted_value
    try:
        return _fernet.decrypt(encrypted_value.encode()).decode()
    except Exception:
        # Если расшифровать не удалось (например, старый пароль), возвращаем как есть
        return encrypted_value