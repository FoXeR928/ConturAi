#!/usr/bin/env bash
set -e

MODE=${1:-"full"}

echo "=================================================="
echo "  ConturAI - Установка (режим: $MODE)"
echo "=================================================="

# 1. Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker не найден."
    exit 1
fi

# 2. Создание .env
if [ ! -f .env ]; then
    python3 scripts/generate_env.py
else
    echo "[OK] Файл .env уже существует."
fi

# 3. Функции запуска
run_backend() {
    echo "[INFO] Сборка и запуск БД, vLLM и Бэкенда..."
    docker compose up -d --build postgres vllm backend
    
    echo "[INFO] Ожидание PostgreSQL..."
    sleep 10
    
    echo "[INFO] Инициализация БД..."
    docker compose exec -T backend python scripts/manage.py init-db
    
    echo "[INFO] Создание администратора..."
    docker compose exec -T backend python scripts/manage.py reset-admin
}

run_frontend() {
    echo "[INFO] Сборка и запуск Фронтенда..."
    docker compose up -d --build frontend
}

case $MODE in
    full)
        run_backend
        run_frontend
        ;;
    backend|test)
        run_backend
        ;;
    frontend)
        run_frontend
        ;;
    *)
        echo "[ERROR] Неизвестный режим: $MODE"
        echo "Доступные режимы: full, backend, frontend, test"
        exit 1
        ;;
esac

echo "=================================================="
echo "  Установка завершена (режим: $MODE)"
echo "=================================================="
if [[ "$MODE" == "full" || "$MODE" == "frontend" ]]; then
    echo "Frontend: http://localhost:3000"
fi
if [[ "$MODE" == "full" || "$MODE" == "backend" || "$MODE" == "test" ]]; then
    echo "API:      http://localhost:8000/docs"
    echo "Status:   http://localhost:8000/status"
fi
echo "=================================================="