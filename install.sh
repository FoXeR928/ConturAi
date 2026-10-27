#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

G="\033[0;32m"; R="\033[0;31m"; Y="\033[1;33m"; N="\033[0m"
log()  { echo -e "${G}[INFO]${N}  $*"; }
warn() { echo -e "${Y}[WARN]${N}  $*"; }
err()  { echo -e "${R}[ERROR]${N} $*" >&2; }

if [ "$EUID" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi
has() { command -v "$1" >/dev/null 2>&1; }

ensure_docker_running() {
    if docker info >/dev/null 2>&1; then return; fi
    log "Запускаю Docker..."
    if has systemctl; then $SUDO systemctl start docker || true; fi
    for _ in $(seq 1 30); do
        docker info >/dev/null 2>&1 && return
        sleep 2
    done
    err "Docker не запустился"; exit 1
}

prepare() {
    has docker || { err "Docker не установлен"; exit 1; }
    docker compose version >/dev/null 2>&1 || { err "Docker Compose не установлен"; exit 1; }
    ensure_docker_running
}

dc() { docker compose "$@"; }
exec_backend() { dc exec -T backend python scripts/manage.py "$@"; }

db_user() { grep '^DB_USER=' .env | cut -d= -f2; }
db_name() { grep '^DB_NAME=' .env | cut -d= -f2; }

download_models() {
    dc run --rm --no-deps \
        -v "$(pwd)/models:/models" \
        -e HF_HUB_OFFLINE=0 \
        -e TRANSFORMERS_OFFLINE=0 \
        -e HF_DATASETS_OFFLINE=0 \
        backend python scripts/manage.py download-models "$@"
}

regen_lock() {
    if [ ! -f backend/pyproject.toml ]; then
        err "Не найден backend/pyproject.toml — не могу пересобрать uv.lock"
        exit 1
    fi

    log "Пересборка uv.lock..."
    set +e
    docker run --rm \
        -v "$(pwd)/backend:/app" \
        -w /app \
        -e UV_PROJECT_ENVIRONMENT=/tmp/uv-venv \
        python:3.12-slim \
        sh -c "pip install --quiet uv==0.5.11 && uv lock"
    local rc=$?
    set -e

    if [ "$rc" -ne 0 ]; then
        err "Не удалось пересобрать uv.lock (код $rc)"
        exit 1
    fi
    log "uv.lock пересобран"
}

gen_password() { LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32; }

setup_env() {
    if [ -f .env ]; then
        log ".env уже существует — пароль сохранён"
        return
    fi
    log "Создаю .env с новым паролем..."
    local db_pass=$(gen_password)
    sed -e "s|^DB_USER=.*|DB_USER=conturai_user|" \
        -e "s|^DB_PASSWORD=.*|DB_PASSWORD=${db_pass}|" \
        .env.example > .env
}

update_env() {
    local key="$1" value="$2"
    if grep -q "^${key}=" .env 2>/dev/null; then
        if sed --version >/dev/null 2>&1; then
            sed -i "s|^${key}=.*|${key}=${value}|" .env
        else
            sed -i '' "s|^${key}=.*|${key}=${value}|" .env
        fi
    else
        echo "${key}=${value}" >> .env
    fi
}

pick_model() {
    echo ""
    echo "Выберите модель ИИ:"
    echo "  1) Qwen2.5-0.5B-Instruct (CPU, слабый ПК)"
    echo "  2) Qwen2.5-1.5B-Instruct (8-12 ГБ VRAM)"
    echo "  3) Qwen2.5-3B-Instruct   (16 ГБ VRAM)"
    echo "  4) Qwen2.5-7B-Instruct   (24+ ГБ VRAM)"
    read -r -p "Номер [2]: " m
    m="${m:-2}"

    local model_name model_file max_len
    case "$m" in
        1) model_name="Qwen/Qwen2.5-0.5B-Instruct"; model_file="Qwen2.5-0.5B-Instruct"; max_len="2048";;
        2) model_name="Qwen/Qwen2.5-1.5B-Instruct"; model_file="Qwen2.5-1.5B-Instruct"; max_len="2048";;
        3) model_name="Qwen/Qwen2.5-3B-Instruct"; model_file="Qwen2.5-3B-Instruct"; max_len="4096";;
        4) model_name="Qwen/Qwen2.5-7B-Instruct"; model_file="Qwen2.5-7B-Instruct"; max_len="8192";;
        *) model_name="Qwen/Qwen2.5-1.5B-Instruct"; model_file="Qwen2.5-1.5B-Instruct"; max_len="2048";;
    esac

    update_env "VLLM_MODEL_PATH"   "/models/${model_file}"
    update_env "VLLM_SERVED_NAME"  "local-model"
    update_env "VLLM_MAX_MODEL_LEN" "${max_len}"
    update_env "MODELS_TO_DOWNLOAD" "intfloat/multilingual-e5-large:multilingual-e5-large,BAAI/bge-reranker-v2-m3:bge-reranker-v2-m3,${model_name}:${model_file}"
    update_env "EMBEDDING_MODEL_PATH" "/models/multilingual-e5-large"
    update_env "EMBEDDING_DIM" "1024"
}

use_platform() {
    local platform="$1"
    local src="templates/docker-compose.${platform}.yml"
    [ -f "$src" ] || { err "Не найден $src"; exit 1; }
    cp "$src" docker-compose.yml
    log "docker-compose.yml перезаписан ($platform)"

    case "$platform" in
        nvidia)
            update_env "PYTORCH_INDEX" "https://download.pytorch.org/whl/cu121"
            update_env "VLLM_IMAGE" "vllm/vllm-openai:latest"
            ;;
        amd)
            update_env "PYTORCH_INDEX" "https://download.pytorch.org/whl/rocm6.1"
            update_env "VLLM_IMAGE" "rocm/vllm:latest"
            ;;
        *)
            update_env "PYTORCH_INDEX" "https://download.pytorch.org/whl/cpu"
            update_env "VLLM_IMAGE" "vllm/vllm-openai-cpu:latest"
            ;;
    esac
}

pick_platform() {
    echo ""
    echo "Выберите платформу:"
    echo "  1) nvidia"
    echo "  2) amd"
    echo "  3) cpu"
    read -r -p "Номер [1]: " p
    p="${p:-1}"
    case "$p" in
        nvidia|1) MODE=nvidia;;
        amd|2)    MODE=amd;;
        cpu|3)    MODE=cpu;;
        *) err "Неверный выбор"; return 1;;
    esac
    setup_env
    use_platform "$MODE"
    pick_model
}

# --- Проверки после старта ---

wait_for_postgres() {
    log "Ожидание PostgreSQL..."
    for _ in $(seq 1 40); do
        dc exec -T postgres pg_isready -U "$(db_user)" >/dev/null 2>&1 && break
        sleep 2
    done
}

check_db_password() {
    dc exec -T postgres psql -U "$(db_user)" -d "$(db_name)" -c "SELECT 1" >/dev/null 2>&1
}

admin_exists() {
    local count
    count=$(dc exec -T postgres psql -U "$(db_user)" -d "$(db_name)" -tAc \
        "SELECT count(*) FROM users WHERE login='admin'" 2>/dev/null | tr -d ' \n')
    [ "${count:-0}" -gt 0 ]
}

ensure_admin() {
    if admin_exists; then
        log "Администратор уже существует — пароль не меняю."
    else
        log "Создание администратора..."
        exec_backend reset-admin
    fi
}

# --- Установка с нуля ---

containers_exist() {
    [ -n "$(dc ps -a --quiet 2>/dev/null || true)" ]
}

full_install() {
    prepare
    if [ -f .env ]; then
        warn ".env уже существует! Если вы хотите переустановить всё с нуля, используйте пункт 'Полная переустановка'."
        read -r -p "Продолжить обновление существующей установки? (y/N): " ok
        [ "$ok" = "y" ] || return 1
    fi

    pick_platform || return 1

    if containers_exist; then
        warn "Контейнеры уже запущены — пересоздаю (данные сохраняются)"
        dc down --remove-orphans || true
    fi

    regen_lock
    log "Сборка и запуск контейнеров..."
    dc up -d --build

    wait_for_postgres

    if ! check_db_password; then
        err "Пароль в .env не совпадает с паролем в pgdata."
        echo "Выберите пункт 3 (Полная переустановка), чтобы сбросить БД."
        return 1
    fi

    log "Скачивание моделей..."
    download_models

    log "Инициализация схемы БД..."
    exec_backend init-db

    ensure_admin

    log "Установка завершена."
    echo "Frontend: http://localhost:3000"
    echo "API:      http://localhost:8000/docs"
}

# --- Обновление (сохраняет данные) ---

update_install() {
    prepare
    if [ ! -f .env ]; then
        err "Файл .env не найден. Похоже, проект еще не установлен. Используйте пункт 1 (Установка)."
        return 1
    fi

    log "Обновление контейнеров и кода (данные сохраняются)..."
    
    # 1. Пересобираем uv.lock на случай добавления новых библиотек в pyproject.toml
    regen_lock

    # 2. Пересобираем образы и перезапускаем
    dc down --remove-orphans || true
    dc up -d --build

    # 3. Ждем БД
    wait_for_postgres

    if ! check_db_password; then
        err "Пароль в .env не совпадает с паролем в pgdata. Обратитесь к администратору."
        return 1
    fi

    # 4. Применяем миграции БД (добавление новых колонок/таблиц)
    log "Применение миграций БД (migrate)..."
    exec_backend migrate

    # 5. Докачиваем новые модели (если изменился список MODELS_TO_DOWNLOAD)
    log "Проверка моделей..."
    download_models

    log "Обновление успешно завершено!"
}

# --- Полная переустановка ---

full_reinstall() {
    prepare
    warn "Это УДАЛИТ базу данных, чаты, документы и пересоздаст .env."
    read -r -p "Продолжить? (y/N): " ok
    [ "$ok" = "y" ] || { log "Отменено"; return 1; }

    if containers_exist; then
        dc down -v --remove-orphans || true
    else
        docker volume rm conturai_pgdata conturai_app_data 2>/dev/null || true
    fi

    rm -f .env
    pick_platform || return 1

    regen_lock
    dc up -d --build
    wait_for_postgres

    log "Скачивание моделей..."
    download_models
    log "Инициализация БД..."
    exec_backend init-db
    log "Создание администратора..."
    exec_backend reset-admin

    log "Полная переустановка завершена."
}

containers_menu() {
    prepare
    while true; do
        echo ""
        echo "--- Контейнеры ---"
        echo "  1) up -d          2) stop          3) restart"
        echo "  4) up -d --build  5) down          6) down -v"
        echo "  7) logs -f        8) ps            0) Назад"
        read -r -p "Номер: " c
        case "$c" in
            1) dc up -d;;
            2) dc stop;;
            3) dc restart;;
            4) dc up -d --build;;
            5) dc down --remove-orphans;;
            6) read -r -p "Удалить тома с БД? (y/N): " ok; [ "$ok" = "y" ] && dc down -v;;
            7) dc logs -f;;
            8) dc ps;;
            0) return;;
        esac
    done
}

manage_menu() {
    prepare
    while true; do
        echo ""
        echo "--- manage.py ---"
        echo "  1) init-db              2) reset-admin"
        echo "  3) download-models      4) download-models --force"
        echo "  5) set-llm              6) reembed (переиндексация)"
        echo "  7) backup (резервная копия)"
        echo "  8) migrate (применить миграции)"
        echo "  0) Назад"
        read -r -p "Номер: " m
        case "$m" in
            1) exec_backend init-db;;
            2) exec_backend reset-admin;;
            3) download_models;;
            4) download_models --force;;
            5)
                read -r -p "model: " model
                read -r -p "temperature: " temp
                args=""
                [ -n "$model" ] && args+=" --model $model"
                [ -n "$temp" ]  && args+=" --temperature $temp"
                exec_backend set-llm $args
                ;;
            6) exec_backend reembed;;
            7) exec_backend backup;;
            8) exec_backend migrate;;
            0) return;;
        esac
    done
}

while true; do
    echo ""
    echo "=================================================="
    echo "  ConturAI"
    echo "=================================================="
    echo "  1) Установка (с нуля)"
    echo "  2) Обновление (сохранить данные)"
    echo "  3) Полная переустановка (сброс БД)"
    echo "  4) Управление контейнерами"
    echo "  5) Команды manage.py"
    echo "  6) Выход"
    read -r -p "Номер [1]: " choice
    case "${choice:-1}" in
        1) full_install;;
        2) update_install;;
        3) full_reinstall;;
        4) containers_menu;;
        5) manage_menu;;
        6) exit 0;;
        *) err "Неверный выбор";;
    esac
done