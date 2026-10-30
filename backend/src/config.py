from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "conturai-backend"
    debug: bool = False

    secret_key: str = "dev-secret-change-me-please"
    token_expire_minutes: int = 60 * 24

    admin_username: str = "admin"
    admin_password: str = "admin123"

    database_url: str = "sqlite+aiosqlite:///./data/conturai.db"
    plugins_dir: str = "./plugins"

    conturai_manager_url: str = "http://127.0.0.1:8080"

    # "docker" — endpoint = http://{container_name}:{internal_port}
    # "local"  — endpoint = http://localhost:{host_port}
    plugin_endpoint_mode: str = "docker"

    cors_origins: str = "*"


settings = Settings()