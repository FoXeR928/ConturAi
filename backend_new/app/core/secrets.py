import os
import secrets as _secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import jwt
from loguru import logger

from app.core.config import settings

# ==============================================================================
# БЛОК 1: ИНИЦИАЛИЗАЦИЯ ПУТЕЙ И СОЗДАНИЕ ПАПОК
# ==============================================================================

# Получаем абсолютные пути к папкам данных, логов и секретов.
# Метод .resolve() превращает относительный путь (./data) в абсолютный (например, /app/data).
DATA_DIR = Path(settings.data_dir).resolve()
LOGS_DIR = DATA_DIR / "logs"
SECRET_DIR = DATA_DIR / "secret"

# Гарантируем, что эти папки существуют при старте приложения.
# parents=True создает все промежуточные папки (если их нет).
# exist_ok=True предотвращает ошибку, если папка уже существует.
for _d in (DATA_DIR, LOGS_DIR, SECRET_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Пути к конкретным файлам
LOG_FILE = LOGS_DIR / "app.log"
JWT_KEY_FILE = SECRET_DIR / "secret.jwt"


# ==============================================================================
# БЛОК 2: УПРАВЛЕНИЕ СЕКРЕТНЫМ КЛЮЧОМ JWT
# ==============================================================================

def load_or_create_jwt_key() -> str:
    """
    Загружает секретный ключ для подписи JWT из файла.
    Если файла нет (первый запуск), генерирует новый безопасный ключ, 
    сохраняет его на диск и выставляет права доступа 600 (только владелец может читать/писать).
    """
    # Если файл существует, читаем ключ
    if JWT_KEY_FILE.exists():
        key = JWT_KEY_FILE.read_text(encoding="utf-8").strip()
        if key:
            return key

    # Если файла нет или он пуст, генерируем новый ключ длиной 64 байта (в URL-safe формате)
    key = _secrets.token_urlsafe(64)
    JWT_KEY_FILE.write_text(key, encoding="utf-8")
    
    # Ограничиваем права доступа. 0o600 — это rw------- (чтение/запись только для владельца).
    # Это критически важно для безопасности в Linux.
    JWT_KEY_FILE.chmod(0o600)
    
    logger.warning(f"Сгенерирован новый JWT-ключ: {JWT_KEY_FILE}")
    return key


@lru_cache(maxsize=1)
def _jwt_key() -> str:
    """
    Кэшированная обертка для загрузки ключа.
    lru_cache(maxsize=1) означает, что функция выполнится только ОДИН раз за всё время 
    работы приложения. Последующие вызовы будут мгновенно брать ключ из памяти.
    Это защищает диск от постоянного чтения файла при каждом запросе к API.
    """
    return load_or_create_jwt_key()


# ==============================================================================
# БЛОК 3: ГЕНЕРАЦИЯ И ПРОВЕРКА ТОКЕНОВ (JWT)
# ==============================================================================

def create_access_token(
    login: str,
    long_lived: bool = False,
    minutes: int = 30,
    days: int = 7,
) -> str:
    """
    Создает JWT-токен для авторизации.
    
    Параметры:
    - login: Логин пользователя (он попадет в поле "sub" токена).
    - long_lived: Если True, токен будет жить `days` дней (галочка "Запомнить меня").
      Если False, токен живет `minutes` минут (обычный вход).
    - minutes, days: Время жизни токена. Берется из БД (настроек) или дефолта.
    """
    # Вычисляем время жизни токена (timedelta)
    delta = (
        timedelta(days=days)
        if long_lived
        else timedelta(minutes=minutes)
    )
    
    # Формируем полезную нагрузку (payload) токена.
    # "sub" (subject) — стандартное поле, в которое мы кладем логин.
    # "exp" (expiration) — время истечения токена в UTC.
    payload = {"sub": login, "exp": datetime.now(timezone.utc) + delta}
    
    # Подписываем токен алгоритмом HS256 (симметричное шифрование).
    return jwt.encode(payload, _jwt_key(), algorithm="HS256")


def decode_token(token: str) -> str:
    """
    Расшифровывает JWT-токен и возвращает логин пользователя (sub).
    
    Если токен просрочен, подпись неверна или токен подделан, 
    библиотека PyJWT выбросит исключение (InvalidTokenError / ExpiredSignatureError).
    Это исключение будет перехвачено выше (в файле deps.py), и пользователь получит 401.
    """
    payload = jwt.decode(token, _jwt_key(), algorithms=["HS256"])
    return payload["sub"]