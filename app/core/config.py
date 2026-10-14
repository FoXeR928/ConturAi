from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RAGI_",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Ragi_AI"
    app_port: int = 8000
    debug: bool = False

    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "ragi"
    db_user: str = "ragi"
    db_password: str = "ragi"
    auto_create_schema: bool = False

    token_expire_minutes: int = 30
    token_expire_days: int = 7

    vllm_base_url: str = "http://vllm:8000/v1"
    vllm_api_key: str = "EMPTY"
    vllm_model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    vllm_temperature: float = 0.7
    vllm_max_tokens: int = 2048

    embedding_model: str = "intfloat/multilingual-e5-large"
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