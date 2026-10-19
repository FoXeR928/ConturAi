#!/usr/bin/env bash
set -e

echo "🚀 Запуск установки ConturAI..."

# 1. Генерируем .env, если его нет
if [ ! -f .env ]; then
    echo "🔧 Генерация конфигурации..."
    # Простой генератор паролей (или можно вызвать ваш python-скрипт)
    DB_PASS=$(openssl rand -hex 16)
    JWT_KEY=$(openssl rand -hex 32)
    
    cat <<EOF > .env
APP_NAME=ConturAI
APP_PORT=8000
DEBUG=false

DB_HOST=postgres
DB_PORT=5432
DB_NAME=conturai
DB_USER=conturai
DB_PASSWORD=${DB_PASS}

TOKEN_EXPIRE_MINUTES=30
TOKEN_EXPIRE_DAYS=7

VLLM_BASE_URL=http://vllm:8000/v1
VLLM_API_KEY=EMPTY
VLLM_MODEL_NAME=local-model
VLLM_TEMPERATURE=0.7
VLLM_MAX_TOKENS=1024

DATA_DIR=/app/data
MODELS_DIR=/models
EMBEDDING_MODEL_PATH=/models/multilingual-e5-large
EMBEDDING_DIM=1024

HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
EOF
    echo "✅ .env создан"
fi

# 2. Собираем и запускаем контейнеры (кроме бэкенда, чтобы сначала настроить БД)
echo "📦 Сборка образов..."
docker compose build

echo "⏳ Запуск базы данных и vLLM..."
docker compose up -d postgres vllm

echo "⏳ Ожидание готовности PostgreSQL..."
until docker compose exec -T postgres pg_isready -U conturai > /dev/null 2>&1; do
    sleep 2
done

# 3. Инициализация БД
echo "🗄️ Инициализация базы данных..."
docker compose run --rm backend python scripts/manage.py init-db

# 4. Создание администратора
echo "🔑 Создание администратора..."
docker compose run --rm backend python scripts/manage.py reset-admin

# 5. Запуск бэкенда и фронтенда
echo "🚀 Запуск приложения..."
docker compose up -d backend frontend

echo "================================================="
echo "✅ ConturAI успешно запущен!"
echo "🌐 Веб-интерфейс: http://localhost:3000"
echo "📖 Swagger UI:    http://localhost:8000/docs"
echo "❤️  Статус:        http://localhost:8000/status"
echo ""
echo "Проверьте логи для получения пароля администратора:"
echo "docker compose logs backend | grep -A 2 'ДАННЫЕ ДЛЯ ВХОДА'"
echo "================================================="