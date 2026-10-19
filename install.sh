#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Установка ConturAI..."

# 1. Генерируем .env с паролями, если его нет
if [ ! -f backend/.env ]; then
    cd backend
    # Предполагается, что uv установлен
    uv run python scripts/setup_env.py
    cd ..
fi

# 2. Поднимаем базу и vLLM
echo "⏳ Запуск базы данных и vLLM..."
docker compose up -d postgres vllm

# 3. Ждем готовности БД
until docker compose exec -T postgres pg_isready -U $(grep DB_USER backend/.env | cut -d '=' -f2) > /dev/null 2>&1; do
    echo "Ожидание PostgreSQL..."
    sleep 2
done

# 4. Инициализация схемы БД
echo "🗄️ Инициализация базы данных..."
docker compose run --rm backend python scripts/manage.py init-db

# 5. Создание админа
echo "🔑 Создание администратора..."
docker compose run --rm backend python scripts/manage.py reset-admin

# 6. Запуск бэкенда
echo "🚀 Запуск бэкенда..."
docker compose up -d backend

echo "================================================="
echo "✅ ConturAI запущен!"
echo "Проверьте логи для получения пароля администратора:"
echo "docker compose logs backend | grep -A 2 'ДАННЫЕ ДЛЯ ВХОДА'"
echo "================================================="