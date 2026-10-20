#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "  ConturAI - установка"
echo "=================================================="
echo ""
echo "Выберите платформу для запуска vLLM:"
echo "  1) NVIDIA GPU (CUDA)"
echo "  2) AMD GPU (ROCm)"
echo "  3) CPU (тест / без GPU)"
echo "  4) Только бэкенд (без фронтенда и vLLM)"
echo "  5) Только фронтенд"
echo ""
read -r -p "Введите номер [1]: " PLATFORM
PLATFORM="${PLATFORM:-1}"

case "$PLATFORM" in
    1) MODE="nvidia";;
    2) MODE="amd";;
    3) MODE="cpu";;
    4) MODE="backend-only";;
    5) MODE="frontend-only";;
    *) echo "[ERROR] Неверный выбор: $PLATFORM"; exit 1;;
esac

echo ""
echo "[INFO] Выбран режим: $MODE"
echo ""

# --- Проверка Docker ---
if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker не найден. Установите Docker и Docker Compose."
    exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "[ERROR] Docker Compose не найден. Установите плагин docker-compose-plugin."
    exit 1
fi
echo "[OK] Docker и Docker Compose найдены."

# --- Python для generate_env.py ---
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 не найден. Установите Python 3.11+."
    exit 1
fi
echo "[OK] Python найден: $(python3 --version)"

# --- 1. .env ---
if [ ! -f .env ]; then
    echo ""
    echo "[INFO] Генерация .env с безопасными паролями..."
    python3 scripts/generate_env.py
else
    echo "[OK] .env уже существует, используем его."
fi

# --- 2. Выбор PYTORCH_INDEX ---
case "$MODE" in
    nvidia)
        PYTORCH_INDEX="https://download.pytorch.org/whl/cu121"
        ;;
    amd)
        PYTORCH_INDEX="https://download.pytorch.org/whl/rocm6.1"
        ;;
    *)
        PYTORCH_INDEX="https://download.pytorch.org/whl/cpu"
        ;;
esac

# Обновляем .env
if grep -q '^PYTORCH_INDEX=' .env; then
    sed -i.bak "s|^PYTORCH_INDEX=.*|PYTORCH_INDEX=${PYTORCH_INDEX}|" .env
else
    echo "" >> .env
    echo "PYTORCH_INDEX=${PYTORCH_INDEX}" >> .env
fi
echo "[OK] PYTORCH_INDEX=${PYTORCH_INDEX}"

# --- 3. Выбор compose override ---
COMPOSE_FILES="-f docker-compose.yml"
case "$MODE" in
    amd)
        if [ -f docker-compose.amd.yml ]; then
            COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.amd.yml"
        fi
        ;;
    cpu)
        if [ -f docker-compose.cpu.yml ]; then
            COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.cpu.yml"
        fi
        ;;
    backend-only)
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.cpu.yml"
        ;;
    frontend-only)
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.cpu.yml"
        ;;
esac

# --- 4. Скачивание моделей ---
if [ "$MODE" != "frontend-only" ]; then
    echo ""
    echo "[INFO] Скачивание моделей в ./models (это может занять время)..."
    docker compose $COMPOSE_FILES run --rm backend \
        python scripts/manage.py download-models
    echo "[OK] Модели скачаны."
fi

# --- 5. Запуск контейнеров ---
echo ""
echo "[INFO] Сборка и запуск контейнеров..."
case "$MODE" in
    backend-only)
        docker compose $COMPOSE_FILES up -d --build postgres backend
        ;;
    frontend-only)
        docker compose $COMPOSE_FILES up -d --build frontend
        ;;
    *)
        docker compose $COMPOSE_FILES up -d --build
        ;;
esac

# --- 6. Ожидание БД и инициализация ---
if [ "$MODE" != "frontend-only" ]; then
    echo ""
    echo "[INFO] Ожидание PostgreSQL..."
    for i in $(seq 1 30); do
        if docker compose $COMPOSE_FILES exec -T postgres \
            pg_isready -U "$(grep '^DB_USER=' .env | cut -d= -f2)" >/dev/null 2>&1; then
            echo "[OK] PostgreSQL готов."
            break
        fi
        sleep 2
    done

    echo ""
    echo "[INFO] Инициализация БД, промтов и llm_configs..."
    docker compose $COMPOSE_FILES exec -T backend \
        python scripts/manage.py init-db

    echo ""
    echo "[INFO] Создание администратора..."
    docker compose $COMPOSE_FILES exec -T backend \
        python scripts/manage.py reset-admin
fi

# --- 7. Итог ---
echo ""
echo "=================================================="
echo "  Установка завершена (режим: $MODE)"
echo "=================================================="
case "$MODE" in
    frontend-only)
        echo "Frontend: http://localhost:3000"
        ;;
    backend-only)
        echo "API:    http://localhost:8000/docs"
        echo "Status: http://localhost:8000/status"
        ;;
    *)
        echo "Frontend: http://localhost:3000"
        echo "API:      http://localhost:8000/docs"
        echo "Status:   http://localhost:8000/status"
        echo "vLLM:     http://localhost:8080/v1"
        ;;
esac
echo ""
echo "Логин и пароль администратора — см. вывод reset-admin выше."
echo "Для изменения параметров LLM без перезапуска:"
echo "  docker compose exec backend python scripts/manage.py set-llm --model <имя> --temperature 0.5"
echo "=================================================="