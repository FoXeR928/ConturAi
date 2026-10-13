from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RAGI_",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_name: str = "Ragi_AI"
    app_port: int = 8000
    debug: bool = False

    # Database
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "ragi"
    db_user: str = "ragi"
    db_password: str = "ragi"
    auto_create_schema: bool = False  # если True — создаёт таблицы при старте

    # Auth
    secret_key: str = "change-me"
    token_expire_minutes: int = 30
    token_expire_days: int = 7

    # vLLM
    vllm_base_url: str = "http://vllm:8000/v1"
    vllm_api_key: str = "EMPTY"
    vllm_model: str = "Qwen/Qwen2.5-7B-Instruct"
    vllm_temperature: float = 0.7
    vllm_max_tokens: int = 2048

    # Embeddings / RAG
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_dim: int = 1024
    rag_search_limit: int = 5
    rag_batch_size: int = 64
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 100

    # Default admin
    default_admin_login: str = "admin"
    default_admin_password: str = "admin"
    default_admin_name: str = "админ"
    system_login: str = "system"

    # AI prompts
    ai_name: str = "Раги"
    system_prompt: str = (
        "Ты - {name}, твоя задача отвечать на вопросы используя информацию из базы, "
        "а если информации нет — генерировать ответ самостоятельно и добавлять "
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