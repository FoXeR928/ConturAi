#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "=================================================="
echo "  ConturAI - Установка"
echo "=================================================="
echo ""
echo "Выберите режим установки:"
echo "  1) NVIDIA GPU (CUDA)           — полный стек"
echo "  2) AMD GPU (ROCm)              — полный стек"
echo "  3) CPU (8+ ГБ ОЗУ)             — полный стек"
echo "  4) Слабый ПК (4–8 ГБ ОЗУ, CPU) — легкие модели"
echo "  5) Только backend (без vLLM)   — API + БД"
echo "  6) Только frontend             — интерфейс"
echo ""
read -r -p "Введите номер: " PLATFORM
PLATFORM="${PLATFORM:-1}"

case "$PLATFORM" in
    1) MODE="nvidia";       COMPOSE_BASE="-f docker-compose.yml";;
    2) MODE="amd";          COMPOSE_BASE="-f docker-compose.yml";; # Изменено: amd теперь основной в docker-compose.yml
    3) MODE="cpu";          COMPOSE_BASE="-f docker-compose.yml -f docker-compose.cpu.yml";;
    4) MODE="dev";          COMPOSE_BASE="-f docker-compose.dev.yml";;
    5) MODE="backend-only"; COMPOSE_BASE="-f docker-compose.yml -f docker-compose.cpu.yml";;
    6) MODE="frontend-only";COMPOSE_BASE="-f docker-compose.yml";;
    *) echo "[ERROR] Неверный выбор"; exit 1;;
esac

echo ""
echo "[INFO] Режим: $MODE"
echo ""

# --- Проверки ---
command -v docker >/dev/null 2>&1 || { echo "[ERROR] Docker не найден."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "[ERROR] Docker Compose не найден."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] python3 не найден."; exit 1; }

# --- 1. .env ---
if [ ! -f .env ]; then
    echo "[INFO] Генерация .env..."
    if [ -f scripts/generate_env.py ]; then
        python3 scripts/generate_env.py
    elif [ -f backend/scripts/generate_env.py ]; then
        python3 backend/scripts/generate_env.py
    else
        echo "[ERROR] generate_env.py не найден."
        exit 1
    fi
else
    echo "[OK] .env уже существует."
fi

# --- 2. Параметры моделей под режим ---
case "$MODE" in
    nvidia) PYTORCH_INDEX="https://download.pytorch.org/whl/cu121";;
    amd)    PYTORCH_INDEX="https://download.pytorch.org/whl/rocm6.1";;
    *)      PYTORCH_INDEX="https://download.pytorch.org/whl/cpu";;
esac

if [ "$MODE" = "dev" ]; then
    LLM_MODEL="Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
    EMB_MODEL="ibm-granite/granite-embedding-97m-multilingual-r2:granite-embedding-97m-multilingual-r2"
    EMB_PATH="/models/granite-embedding-97m-multilingual-r2"
    EMB_DIM="384"
else
    LLM_MODEL="Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
    EMB_MODEL="intfloat/multilingual-e5-large:multilingual-e5-large"
    EMB_PATH="/models/multilingual-e5-large"
    EMB_DIM="1024"
fi

update_env() {
    local key="$1" value="$2"
    if grep -q "^${key}=" .env; then
        sed -i.bak "s|^${key}=.*|${key}=${value}|" .env
        rm -f .env.bak # Чистим за собой временные файлы sed
    else
        echo "${key}=${value}" >> .env
    fi
}

update_env "PYTORCH_INDEX" "$PYTORCH_INDEX"
update_env "EMBEDDING_MODEL_PATH" "$EMB_PATH"
update_env "EMBEDDING_DIM" "$EMB_DIM"
update_env "MODELS_TO_DOWNLOAD" "${LLM_MODEL},${EMB_MODEL}"
update_env "HF_HUB_OFFLINE" "0" # Принудительно отключаем оффлайн-режим HuggingFace

echo "[OK] Конфигурация .env обновлена."

# --- 3. Скачивание моделей ---
if [ "$MODE" != "frontend-only" ] && [ "$MODE" != "backend-only" ]; then
    echo ""
    echo "[INFO] Скачивание моделей (может занять время)..."
    docker compose $COMPOSE_BASE run --rm --no-deps backend \
        python scripts/manage.py download-models
    echo "[OK] Модели скачаны."
fi

# --- 4. Запуск контейнеров ---
echo ""
echo "[INFO] Запуск контейнеров..."
case "$MODE" in
    backend-only)  docker compose $COMPOSE_BASE up -d --build postgres backend;;
    frontend-only) docker compose $COMPOSE_BASE up -d --build frontend;;
    *)             docker compose $COMPOSE_BASE up -d --build;;
esac

# --- 5. Инициализация БД ---
if [ "$MODE" != "frontend-only" ]; then
    echo ""
    echo "[INFO] Ожидание PostgreSQL..."
    for _ in $(seq 1 40); do
        # ИСПРАВЛЕНО: Явно указан юзер 'conturai_user' во избежание падения из-за пустого grep
        if docker compose $COMPOSE_BASE exec -T postgres \
            pg_isready -U "conturai_user" >/dev/null 2>&1; then
            echo "[OK] PostgreSQL готов."
            break
        fi
        sleep 2
    done

    echo "[INFO] Инициализация БД..."
    docker compose $COMPOSE_BASE exec -T backend \
        python scripts/manage.py init-db

    echo "[INFO] Создание администратора..."
    docker compose $COMPOSE_BASE exec -T backend \
        python scripts/manage.py reset-admin
fi

# --- 6. Итог ---
echo ""
echo "=================================================="
echo "  Установка завершена ($MODE)"
echo "=================================================="
case "$MODE" in
    frontend-only) echo "Frontend: http://localhost:3000";;
    backend-only)
        echo "API:      http://localhost:8000/docs"
        echo "Status:   http://localhost:8000/status";;
    *)
        echo "Frontend: http://localhost:3000"
        echo "API:      http://localhost:8000/docs"
        echo "Status:   http://localhost:8000/status"
        echo "vLLM:     http://localhost:8080/v1";;
esac
echo ""
echo "Пароль администратора — см. вывод reset-admin выше."
echo "=================================================="
