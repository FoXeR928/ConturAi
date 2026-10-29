FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN pip install --upgrade pip && \
    pip install \
        "fastapi>=0.115.0" \
        "uvicorn[standard]>=0.30.0" \
        "httpx>=0.27.0" \
        "pydantic>=2.8.0" \
        "asyncpg>=0.29.0" \
        "pyjwt>=2.9.0" \
        "bcrypt>=4.2.0"

COPY app ./app

RUN mkdir -p /app/plugins

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]