# ConturAI

ConturAI — это локальный AI-ассистент с поддержкой RAG (Retrieval-Augmented Generation). Проект объединяет современный веб-интерфейс, высокопроизводительный инференс больших языковых моделей через vLLM и векторный поиск на базе PostgreSQL (pgvector).

Система полностью автономна и может работать без доступа к интернету (offline).

## Ключевые возможности

- Полностью локальная работа без внешних API.
- RAG на базе PostgreSQL + pgvector (HNSW индекс).
- Асинхронный бэкенд (FastAPI + SQLAlchemy).
- Инференс моделей через vLLM (OpenAI-совместимый API).
- Современный фронтенд (React, TypeScript, Tailwind CSS).
- Поддержка загрузки документов (PDF, DOCX, XLSX) и OCR.
- Гибкая настройка через переменные окружения.
- Полная контейнеризация (Docker Compose).

## Технологический стек

- **Backend:** Python 3.11, FastAPI, SQLAlchemy (async), uv.
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Nginx.
- **База данных:** PostgreSQL 16 + pgvector.
- **AI / LLM:** vLLM, SentenceTransformers (multilingual-e5-large).
- **Инфраструктура:** Docker, Docker Compose.

## Структура проекта

```text
conturai/
├── backend/               # Исходный код бэкенда (FastAPI)
│   ├── app/               # Основной код приложения
│   ├── scripts/           # Скрипты управления (manage.py)
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/              # Исходный код фронтенда (React + Vite)
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── models/                # Локальные веса моделей (HuggingFace)
├── scripts/               # Вспомогательные скрипты (генерация .env)
├── docker-compose.yml     # Конфигурация Docker
├── install.sh             # Скрипт установки для Linux/macOS
├── install.bat            # Скрипт установки для Windows
└── .env.example           # Шаблон переменных окружения
```

## Требования

- Docker и Docker Compose (версия 2.0+).
- Python 3.11+ (только для генерации `.env` файла перед сборкой).
- Оборудование: **NVIDIA GPU**, **AMD GPU (ROCm)** или **CPU** (см. раздел «Варианты запуска»).

## Варианты запуска `docker-compose`

Выбор варианта зависит от вашего оборудования. Все три варианта отличаются только сервисом `vllm` (и его `deploy`-секцией). PostgreSQL, бэкенд и фронтенд работают одинаково везде.

### Вариант 1. NVIDIA GPU (по умолчанию)

Используется официальный образ `vllm/vllm-openai:latest` с пробросом GPU через `nvidia-container-toolkit`.

```yaml
name: conturai

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: conturai_postgres
    environment:
      POSTGRES_USER: ${DB_USER:-conturai_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-conturai}
      POSTGRES_DB: ${DB_NAME:-conturai}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-conturai_user} -d ${DB_NAME:-conturai}"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  # --- NVIDIA GPU ---
  vllm:
    image: vllm/vllm-openai:latest
    container_name: conturai_vllm
    command: >
      --model /models/Qwen2.5-0.5B-Instruct
      --served-model-name local-model
      --host 0.0.0.0
      --port 8000
      --max-model-len 4096
      --gpu-memory-utilization 0.85
    environment:
      HF_HUB_OFFLINE: "1"
      TRANSFORMERS_OFFLINE: "1"
    ports:
      - "8080:8000"
    volumes:
      - ./models:/models:ro
    ipc: host
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8000/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 30
      start_period: 120s
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
      args:
        PYTORCH_INDEX: ${PYTORCH_INDEX:-https://download.pytorch.org/whl/cpu}
    container_name: conturai_backend
    env_file: .env
    environment:
      DB_HOST: postgres
      VLLM_BASE_URL: http://vllm:8000/v1
      DATA_DIR: /app/data
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      vllm:
        condition: service_started
    volumes:
      - app_data:/app/data
      - ./models:/models:ro
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: conturai_frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  pgdata:
  app_data:
```

**Требования:** драйвер NVIDIA + установленный `nvidia-container-toolkit`.

### Вариант 2. AMD GPU (ROCm)

Используется образ `rocm/vllm:latest`, GPU пробрасывается через `/dev/kfd` и `/dev/dri`. Убедитесь, что у вас установлены драйверы ROCm и Docker настроен для работы с AMD GPU.

```yaml
name: conturai

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: conturai_postgres
    environment:
      POSTGRES_USER: ${DB_USER:-conturai_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-conturai}
      POSTGRES_DB: ${DB_NAME:-conturai}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-conturai_user} -d ${DB_NAME:-conturai}"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  # --- AMD GPU (ROCm) ---
  vllm:
    image: rocm/vllm:latest
    container_name: conturai_vllm
    command: >
      --model /models/Qwen2.5-0.5B-Instruct
      --served-model-name local-model
      --host 0.0.0.0
      --port 8000
      --max-model-len 4096
    environment:
      HF_HUB_OFFLINE: "1"
      TRANSFORMERS_OFFLINE: "1"
    ports:
      - "8080:8000"
    volumes:
      - ./models:/models:ro
    devices:
      - /dev/kfd
      - /dev/dri
    group_add:
      - video
    security_opt:
      - seccomp:unconfined
    ipc: host
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8000/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 30
      start_period: 300s
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
      args:
        PYTORCH_INDEX: ${PYTORCH_INDEX:-https://download.pytorch.org/whl/cpu}
    container_name: conturai_backend
    env_file: .env
    environment:
      DB_HOST: postgres
      VLLM_BASE_URL: http://vllm:8000/v1
      DATA_DIR: /app/data
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      vllm:
        condition: service_started
    volumes:
      - app_data:/app/data
      - ./models:/models:ro
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: conturai_frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  pgdata:
  app_data:
```

**Требования:** ROCm-совместимая AMD GPU, ROCm-драйверы, Docker. Для тестовой сборки можно также указать `PYTORCH_INDEX=https://download.pytorch.org/whl/rocm6.1` в `.env`.

> Примечание: официальный `rocm/vllm` содержит большие зависимости, скачивание может занять значительное время. Если на тестовой машине нет AMD GPU, используйте вариант 3 (CPU).

### Вариант 3. CPU (без GPU, для тестов и разработки)

Подходит для тестирования всей системы (API, фронтенд, RAG) без GPU. LLM-ответы будут медленными, поэтому этот вариант используется для проверки интеграции, а не для продакшна.

```yaml
name: conturai

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: conturai_postgres
    environment:
      POSTGRES_USER: ${DB_USER:-conturai_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-conturai}
      POSTGRES_DB: ${DB_NAME:-conturai}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-conturai_user} -d ${DB_NAME:-conturai}"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  # --- CPU (без GPU) ---
  # vLLM на CPU работает медленно. Для тестов API без LLM можно
  # полностью удалить сервис `vllm` и `depends_on.vllm` у backend.
  vllm:
    image: vllm/vllm-openai:latest
    container_name: conturai_vllm
    command: >
      --model /models/Qwen2.5-0.5B-Instruct
      --served-model-name local-model
      --host 0.0.0.0
      --port 8000
      --max-model-len 2048
      --dtype float32
    environment:
      HF_HUB_OFFLINE: "1"
      TRANSFORMERS_OFFLINE: "1"
    ports:
      - "8080:8000"
    volumes:
      - ./models:/models:ro
    ipc: host
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
      args:
        PYTORCH_INDEX: ${PYTORCH_INDEX:-https://download.pytorch.org/whl/cpu}
    container_name: conturai_backend
    env_file: .env
    environment:
      DB_HOST: postgres
      VLLM_BASE_URL: http://vllm:8000/v1
      DATA_DIR: /app/data
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      # Если сервис vllm удален, закомментируйте эту зависимость:
      # vllm:
      #   condition: service_started
    volumes:
      - app_data:/app/data
      - ./models:/models:ro
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: conturai_frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  pgdata:
  app_data:
```

**Требования:** достаточно обычного Docker без GPU. На CPU рекомендуется модель `Qwen2.5-0.5B` (маленькая) и `--dtype float32`.
