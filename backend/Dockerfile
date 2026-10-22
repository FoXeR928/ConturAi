FROM python:3.11-slim

# --- ДОБАВЛЯЕМ АРГУМЕНТ ДЛЯ ВЫБОРА ВЕРСИИ TORCH ---
# По умолчанию - CPU (легкий, ~200МБ). 
# Для NVIDIA: https://download.pytorch.org/whl/cu121
# Для AMD: https://download.pytorch.org/whl/rocm6.1
ARG PYTORCH_INDEX=https://download.pytorch.org/whl/cpu

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
    UV_CONCURRENT_DOWNLOADS=4

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-rus poppler-utils curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock* ./

# --- ПОДМЕНЯЕМ URL В PYPROJECT.TOML НА ТОТ, ЧТО ПЕРЕДАЛИ В ARG ---
RUN sed -i "s|https://download.pytorch.org/whl/cpu|${PYTORCH_INDEX}|g" pyproject.toml

# Убираем --frozen, так как мы меняем pyproject.toml на лету
RUN uv sync --no-install-project --no-dev \
    --index-url ${PYTORCH_INDEX}

COPY backend/app ./app
COPY backend/scripts ./scripts

RUN mkdir -p /app/data/logs /app/data/secret

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 8000

CMD ["python", "-m", "app.main"]