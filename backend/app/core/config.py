from pathlib import Path
import tomllib

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_version() -> str:
    try:
        toml_path = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]
    except Exception:
        return "unknown"


APP_VERSION = _get_version()

ADMIN_LOGIN = "admin"
ADMIN_NAME = "админ"
SYSTEM_LOGIN = "system"
SYSTEM_CHAT_ROLE = "assistant"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "ConturAI"
    app_port: int = 8000
    debug: bool = False

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "conturai_db"
    db_user: str = "conturai_user"
    db_password: str = "conturai"

    token_expire_minutes: int = 30
    token_expire_days: int = 7

    data_dir: str = "./data"
    models_dir: str = "./models"

    models_to_download: str = (
        "intfloat/multilingual-e5-large:multilingual-e5-large,"
        "Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
    )

    embedding_model_path: str = "./models/multilingual-e5-large"
    embedding_dim: int = 1024

    reranker_model_path: str = "./models/bge-reranker-v2-m3"

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()