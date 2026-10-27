FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    HF_HOME=/models/.hf \
    SENTENCE_TRANSFORMERS_HOME=/models/.hf \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_DATASETS_OFFLINE=1 \
    UV_HTTP_TIMEOUT=900 \
    UV_CONCURRENT_DOWNLOADS=4 \
    TIKTOKEN_CACHE_DIR=/app/.tiktoken_cache

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-rus poppler-utils curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./

# Устанавливаем строго по lock. Никаких тестов и лишних пакетов.
RUN uv sync --locked --no-install-project --no-dev

# Копируем ТОЛЬКО рабочий код
COPY backend/app ./app
COPY backend/scripts ./scripts

# Создаем папки для логов, секретов и кэша tiktoken
RUN mkdir -p /app/data/logs /app/data/secret /app/.tiktoken_cache

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 8000
CMD ["python", "-m", "app.main"]