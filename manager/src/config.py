from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Режим ---
    # True  = backend/frontend/manager работают как локальные процессы,
    #         Docker используется только для postgres и плагинов.
    # False = весь стек в Docker (production / v3.0).
    local_mode: bool = False
    manager_port: int = 8080

    # --- Инфраструктура ---
    network_name: str = "conturai-mesh-net"
    pg_volume: str = "conturai-pg-data"
    models_volume: str = "conturai-models"

    # --- Имена ---
    postgres_name: str = "conturai-postgres"
    backend_name: str = "conturai-backend"
    frontend_name: str = "conturai-frontend"

    # --- Образы ---
    postgres_image: str = "postgres:16-alpine"
    backend_image: str = "conturai-backend:latest"
    frontend_image: str = "conturai-frontend:latest"
    fallback_image: str = "alpine:3.19"

    # --- Порты (host) ---
    postgres_host_port: int = 5432
    backend_host_port: int = 8000
    frontend_host_port: int = 5173  # Vite dev по умолчанию

    # --- Health-check URL для local_mode ---
    backend_health_url: str = "http://127.0.0.1:8000/api/health"
    frontend_health_url: str = "http://127.0.0.1:5173/"

    # --- Postgres credentials ---
    pg_user: str = "conturai_user"
    pg_password: str = "conturai_secret_change_me"
    pg_db: str = "conturai_db"

    # --- Docker ---
    docker_timeout: int = 120

    @property
    def postgres_env(self) -> dict:
        return {
            "POSTGRES_USER": self.pg_user,
            "POSTGRES_PASSWORD": self.pg_password,
            "POSTGRES_DB": self.pg_db,
        }

    @property
    def backend_env(self) -> dict:
        return {
            "APP_NAME": "ConturAI",
            "APP_PORT": "8000",
            "DEBUG": "false",
            "DB_HOST": self.postgres_name,
            "DB_PORT": "5432",
            "DB_NAME": self.pg_db,
            "DB_USER": self.pg_user,
            "DB_PASSWORD": self.pg_password,
            "TOKEN_EXPIRE_MINUTES": "1440",
            "PLUGINS_DIR": "/app/plugins",
            "CONTURAI_MANAGER_URL": "http://conturai-manager:8080",
        }

    @property
    def frontend_env(self) -> dict:
        return {"BACKEND_URL": f"http://{self.backend_name}:8000"}


settings = Settings()