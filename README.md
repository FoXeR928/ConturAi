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
- NVIDIA GPU (для запуска vLLM). Для тестирования без GPU можно отключить сервис `vllm`.

## Установка и запуск

### Автоматическая установка

Для Linux и macOS:
```bash
chmod +x install.sh
./install.sh full
```

Для Windows (PowerShell или CMD):
```cmd
install.bat full
```

Скрипт автоматически сгенерирует `.env` с безопасными паролями, соберет контейнеры, инициализирует базу данных и создаст администратора. Пароль администратора будет выведен в консоль.

### Ручная установка

1. Создайте файл конфигурации:
   ```bash
   python scripts/generate_env.py
   ```

2. Соберите и запустите контейнеры:
   ```bash
   docker compose up -d --build
   ```

3. Инициализируйте схему базы данных и промты:
   ```bash
   docker compose exec backend python scripts/manage.py init-db
   ```

4. Создайте администратора (пароль будет показан в логах):
   ```bash
   docker compose exec backend python scripts/manage.py reset-admin
   ```

### Скачивание моделей (Offline режим)

Для работы без интернета скачайте модели один раз (на машине с доступом в сеть):
```bash
python scripts/download_models.py
```
Модели будут сохранены в папку `./models` и примонтированы в контейнеры.

## Доступ к сервисам

- **Веб-интерфейс:** `http://localhost:3000`
- **Swagger API:** `http://localhost:8000/docs`
- **Статус сервера:** `http://localhost:8000/status`
- **vLLM (OpenAI API):** `http://localhost:8080/v1`

## Управление и обслуживание

Все команды выполняются внутри контейнера `backend` из корня проекта:

```bash
# Инициализация БД и промтов (при первом запуске)
docker compose exec backend python scripts/manage.py init-db

# Сброс пароля администратора (создает нового, если удален)
docker compose exec backend python scripts/manage.py reset-admin
```

## Режимы установки

Скрипты `install.sh` и `install.bat` поддерживают аргументы:
- `full` (или без аргументов) — полная установка (БД, бэкенд, фронтенд, vLLM).
- `backend` — только БД и бэкенд (для тестирования API).
- `frontend` — только фронтенд.
- `test` — аналогично backend, но с более подробными логами.

## Переменные окружения

Все настройки хранятся в файле `.env` в корне проекта.
Основные параметры:
- `DB_USER`, `DB_PASSWORD`, `DB_NAME` — реквизиты PostgreSQL.
- `VLLM_BASE_URL` — адрес API vLLM.
- `VLLM_MODEL_NAME` — название модели для vLLM.
- `EMBEDDING_MODEL_PATH` — путь к локальной модели эмбеддингов.

Промты (system prompt, user prompt) хранятся в базе данных и могут быть изменены через API (`/prompts/update`) без перезапуска контейнеров.

## Пример `docker-compose.yml`

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
