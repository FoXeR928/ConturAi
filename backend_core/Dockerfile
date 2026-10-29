FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_HTTP_TIMEOUT=300 \
    UV_CONCURRENT_DOWNLOADS=4

# Оставляем только curl для healthcheck (если он нужен)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./

# Устанавливаем строго по lock (теперь это займет секунды, а не минуты)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

COPY backend/app ./app
COPY backend/scripts ./scripts

# Папки для логов и секретов
RUN mkdir -p /app/data/logs /app/data/secret /app/plugins

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 8000
CMD ["python", "-m", "app.main"]