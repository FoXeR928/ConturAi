#!/usr/bin/env bash
set -e

# 1. Поднимаем контейнеры
docker compose up -d --build

# 2. Ждем, пока база данных запустится
echo "Ожидание базы данных..."
sleep 5

# 3. Инициализируем БД
echo "Инициализация БД..."
docker compose exec -T backend python scripts/manage.py init-db

# 4. Создаем админа
echo "Создание администратора..."
docker compose exec -T backend python scripts/manage.py reset-admin

echo "Готово! Сервер запущен на http://localhost:8000"