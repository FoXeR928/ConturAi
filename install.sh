#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PY=$(command -v python3 || command -v python || true)
if [ -z "$PY" ]; then
    echo "[ERROR] Не найден python3/python. Установите Python 3.11+."
    exit 1
fi
if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker не найден."
    exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "[ERROR] Docker Compose не найден."
    exit 1
fi

MANAGE_HOST="$PY backend/scripts/manage.py"
MANAGE_DOCKER="docker compose exec -T backend python scripts/manage.py"
MANAGE_RUN="docker compose run --rm --no-deps backend python scripts/manage.py"

ensure_env() {
    if [ ! -f .env ]; then
        echo "[INFO] Генерация .env..."
        $MANAGE_HOST setup-env
    fi
}

pick_platform() {
    echo ""
    echo "Выберите платформу:"
    echo "  1) nvidia  — GPU NVIDIA (CUDA)"
    echo "  2) amd     — GPU AMD (ROCm)"
    echo "  3) cpu     — CPU, 8+ ГБ ОЗУ"
    echo "  4) dev     — CPU, 4–8 ГБ ОЗУ (лёгкие модели)"
    read -r -p "Номер [1]: " p
    p="${p:-1}"
    case "$p" in
        1) MODE=nvidia;;
        2) MODE=amd;;
        3) MODE=cpu;;
        4) MODE=dev;;
        *) echo "[ERROR] Неверный выбор"; return 1;;
    esac
    ensure_env
    $MANAGE_HOST use-platform "$MODE"
}

full_install() {
    pick_platform || return 1
    echo "[INFO] Скачивание моделей..."
    $MANAGE_RUN download-models
    echo "[INFO] Сборка и запуск контейнеров..."
    docker compose up -d --build
    echo "[INFO] Ожидание PostgreSQL..."
    for _ in $(seq 1 40); do
        if docker compose exec -T postgres \
            pg_isready -U "$(grep '^DB_USER=' .env | cut -d= -f2)" >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done
    echo "[INFO] Инициализация БД и администратора..."
    $MANAGE_DOCKER init-db
    $MANAGE_DOCKER reset-admin
    echo "[OK] Установка завершена."
}

containers_menu() {
    while true; do
        echo ""
        echo "--- Контейнеры ---"
        echo "  1) Запустить (up -d)"
        echo "  2) Остановить (stop)"
        echo "  3) Перезапустить (restart)"
        echo "  4) Пересобрать и запустить (up -d --build)"
        echo "  5) Удалить (down)"
        echo "  6) Удалить вместе с томами (down -v) — ВНИМАНИЕ: удалит БД"
        echo "  7) Логи (follow)"
        echo "  8) Статус (ps)"
        echo "  0) Назад"
        read -r -p "Номер: " c
        case "$c" in
            1) docker compose up -d;;
            2) docker compose stop;;
            3) docker compose restart;;
            4) docker compose up -d --build;;
            5) docker compose down;;
            6) read -r -p "Точно удалить тома с БД? (y/N): " ok
               [ "$ok" = "y" ] && docker compose down -v;;
            7) docker compose logs -f;;
            8) docker compose ps;;
            0) return;;
            *) echo "Неверный выбор";;
        esac
    done
}

manage_menu() {
    ensure_env
    while true; do
        echo ""
        echo "--- manage.py ---"
        echo "  1) setup-env (создать .env)"
        echo "  2) use-platform nvidia"
        echo "  3) use-platform amd"
        echo "  4) use-platform cpu"
        echo "  5) use-platform dev"
        echo "  6) download-models"
        echo "  7) download-models --only ..."
        echo "  8) init-db"
        echo "  9) reset-admin"
        echo " 10) set-llm (интерактивно)"
        echo "  0) Назад"
        read -r -p "Номер: " m
        case "$m" in
            1) $MANAGE_HOST setup-env;;
            2|3|4|5)
               case "$m" in
                   2) P=nvidia;; 3) P=amd;; 4) P=cpu;; 5) P=dev;;
               esac
               $MANAGE_HOST use-platform "$P";;
            6) $MANAGE_RUN download-models;;
            7) read -r -p "repo:name,repo:name: " only
               $MANAGE_RUN download-models --only "$only";;
            8) $MANAGE_DOCKER init-db;;
            9) $MANAGE_DOCKER reset-admin;;
            10)
               read -r -p "model: " model
               read -r -p "temperature: " temp
               read -r -p "max-tokens: " mt
               args=""
               [ -n "$model" ] && args="$args --model $model"
               [ -n "$temp" ]  && args="$args --temperature $temp"
               [ -n "$mt" ]    && args="$args --max-tokens $mt"
               # shellcheck disable=SC2086
               $MANAGE_DOCKER set-llm $args;;
            0) return;;
            *) echo "Неверный выбор";;
        esac
    done
}

while true; do
    echo ""
    echo "=================================================="
    echo "  ConturAI — установка и управление"
    echo "=================================================="
    echo "  1) Полная установка (выбор платформы + модели + БД)"
    echo "  2) Управление контейнерами"
    echo "  3) Команды manage.py"
    echo "  4) Выход"
    read -r -p "Номер [1]: " main_choice
    case "${main_choice:-1}" in
        1) full_install;;
        2) containers_menu;;
        3) manage_menu;;
        4) exit 0;;
        *) echo "Неверный выбор";;
    esac
done