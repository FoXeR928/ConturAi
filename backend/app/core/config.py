from pydantic_settings import BaseSettings, SettingsConfigDict

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
    db_name: str = "conturai"
    db_user: str = "conturai"
    db_password: str = "conturai"

    token_expire_minutes: int = 30
    token_expire_days: int = 7

    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_api_key: str = "EMPTY"
    vllm_model_name: str = "local-model"
    vllm_temperature: float = 0.7
    vllm_max_tokens: int = 2048

    data_dir: str = "./data"
    models_dir: str = "./models"
    embedding_model_path: str = "./models/multilingual-e5-large"
    embedding_dim: int = 1024
    
    rag_search_limit: int = 5
    rag_batch_size: int = 64
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 100

    ai_name: str = "Раги"
    system_prompt: str = (
        "Ты - {name}. Отвечай на вопросы, используя контекст из базы. "
        "Если данных нет — отвечай самостоятельно и добавляй "
        "'Ответ сгенерирован самостоятельно'"
    )
    user_prompt: str = "Контекст: {context}\nВопрос: {quest}"

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

settings = Settings()