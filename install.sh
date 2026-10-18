#!/usr/bin/env bash
set -euo pipefail

echo "Установка ConturAI..."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Создан файл .env"
fi

echo "Сборка контейнеров..."
docker compose build

echo "Запуск базы данных и vLLM (ожидание)..."
docker compose up -d postgres vllm

# Ждем, пока Postgres будет готов
until docker compose exec -T postgres pg_isready -U conturai > /dev/null 2>&1; do
    echo "Ожидание PostgreSQL..."
    sleep 2
done

echo "Инициализация базы данных..."
docker compose run --rm backend python scripts/manage.py init-db

echo "Генерация пароля администратора..."
docker compose run --rm backend python scripts/manage.py reset-admin

echo "Запуск основного приложения..."
docker compose up -d backend

echo "================================================="
echo "ConturAI успешно запущен!"
echo "API: http://localhost:8000/docs"
echo "================================================="