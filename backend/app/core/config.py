from pathlib import Path
import tomllib

from pydantic_settings import BaseSettings, SettingsConfigDict

# ==============================================================================
# БЛОК 1: ЧТЕНИЕ ВЕРСИИ ИЗ PYPROJECT.TOML
# ==============================================================================

def _get_version() -> str:
    """
    Динамически считывает версию проекта из файла pyproject.toml.
    Это нужно, чтобы версия в коде и версия в пакетном менеджере (uv) всегда совпадали.
    Если файл не найден или формат нарушен (например, при запуске из другого места), 
    возвращает "unknown".
    """
    try:
        # Поднимаемся на 3 уровня вверх от config.py до корня проекта, где лежит pyproject.toml
        toml_path = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        with open(toml_path, "rb") as f:
            data = tomllib.load(f) # tomllib встроен в Python 3.11+
            return data["project"]["version"]
    except Exception:
        return "unknown"


# ==============================================================================
# БЛОК 2: СИСТЕМНЫЕ КОНСТАНТЫ (НЕ МЕНЯЮТСЯ ЧЕРЕЗ .ENV)
# ==============================================================================

APP_VERSION = _get_version()

# Захардкоженные имена системных аккаунтов. 
# Они нужны для защиты от случайного удаления/блокировки главного админа.
ADMIN_LOGIN = "admin"
ADMIN_NAME = "админ"

# Служебный аккаунт, от имени которого ИИ пишет ответы в базу данных.
# Благодаря этому в истории чата можно отличить сообщение пользователя от ответа нейросети.
SYSTEM_LOGIN = "system"
SYSTEM_CHAT_ROLE = "assistant"


# ==============================================================================
# БЛОК 3: ОСНОВНОЙ КЛАСС НАСТРОЕК (Pydantic Settings)
# ==============================================================================

class Settings(BaseSettings):
    """
    Класс конфигурации, который автоматически читает переменные окружения из файла .env.
    Если переменная не найдена в .env, используется значение по умолчанию, указанное здесь.
    """
    model_config = SettingsConfigDict(
        env_file=".env",             # Читаем файл .env из корневой папки
        env_file_encoding="utf-8",   # Кодировка файла
        extra="ignore",              # Игнорируем лишние переменные в .env, которых нет в этом классе
        case_sensitive=False,        # DB_HOST и db_host считаются одинаковыми
    )

    # --- Общие настройки приложения ---
    app_name: str = "ConturAI"
    app_port: int = 8000
    debug: bool = False              # Включает подробные логи и SQL-запросы

    # --- Подключение к базе данных (PostgreSQL) ---
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "conturai_db"
    db_user: str = "conturai_user"
    db_password: str = "conturai"

    # --- Настройки JWT-токенов (дефолтные значения, если в БД пусто) ---
    token_expire_minutes: int = 30
    token_expire_days: int = 7

    # --- Пути к папкам (внутри Docker-контейнера) ---
    data_dir: str = "./data"         # Логи, секреты, загрузки
    models_dir: str = "./models"     # Скачанные модели LLM и эмбеддингов

    # --- Список моделей для скачивания (админ может переопределить) ---
    models_to_download: str = (
        "intfloat/multilingual-e5-large:multilingual-e5-large,"
        "Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
    )

    # --- Настройки моделей RAG ---
    embedding_model_path: str = "/models/multilingual-e5-large"
    embedding_dim: int = 1024
    reranker_model_path: str = "/models/bge-reranker-v2-m3"

    # ==========================================================================
    # БЛОК 4: ВЫЧИСЛЯЕМЫЕ СВОЙСТВА (PROPERTIES)
    # ==========================================================================

    @property
    def db_url(self) -> str:
        """
        Формирует строку подключения (DSN) для асинхронного драйвера asyncpg.
        Используется в session.py для создания движка SQLAlchemy.
        Пример: postgresql+asyncpg://conturai_user:pass@postgres:5432/conturai_db
        """
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


# ==============================================================================
# БЛОК 5: ИНИЦИАЛИЗАЦИЯ ЭКЗЕМПЛЯРА (СИНГЛТОН)
# ==============================================================================

# Создаем глобальный объект настроек. 
# При импорте этого файла в любом другом месте программы, 
# pydantic мгновенно прочитает .env и заполнит все поля.
settings = Settings()