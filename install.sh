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
        -e HF_HUB_OFFLINE=0 \
        -e TRANSFORMERS_OFFLINE=0 \
        -e HF_DATASETS_OFFLINE=0 \
        backend python scripts/manage.py download-models "$@"
}

regen_lock() {
    log "Пересборка uv.lock..."
    docker run --rm \
        -v "$(pwd)/backend:/app" \
        -w /app \
        -e UV_PROJECT_ENVIRONMENT=/tmp/uv-venv \
        python:3.12-slim \
        sh -c "pip install --quiet uv==0.5.11 && uv lock"
    if [ $? -ne 0 ]; then
        err "Не удалось пересобрать uv.lock"
        exit 1
    fi
    log "uv.lock пересобран"
}

gen_password() { LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32; }

# --- .env: генерируем ТОЛЬКО если файла нет. Пароль не меняется при повторных запусках.
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

use_platform() {
    local platform="$1"
    local src="templates/docker-compose.${platform}.yml"
    [ -f "$src" ] || { err "Не найден $src"; exit 1; }
    cp "$src" docker-compose.yml
    log "docker-compose.yml перезаписан ($platform)"

    local model_name model_file
    case "$platform" in
        nvidia)
            update_env "PYTORCH_INDEX" "https://download.pytorch.org/whl/cu121"
            model_name="Qwen/Qwen2.5-1.5B-Instruct"
            model_file="Qwen2.5-1.5B-Instruct"
            ;;
        amd)
            update_env "PYTORCH_INDEX" "https://download.pytorch.org/whl/rocm6.1"
            model_name="Qwen/Qwen2.5-1.5B-Instruct"
            model_file="Qwen2.5-1.5B-Instruct"
            ;;
        *)
            update_env "PYTORCH_INDEX" "https://download.pytorch.org/whl/cpu"
            model_name="Qwen/Qwen2.5-0.5B-Instruct"
            model_file="Qwen2.5-0.5B-Instruct"
            ;;
    esac
    update_env "VLLM_MODEL_PATH"   "/models/${model_file}"
    update_env "VLLM_SERVED_NAME"  "local-model"
    update_env "MODELS_TO_DOWNLOAD" "intfloat/multilingual-e5-large:multilingual-e5-large,${model_name}:${model_file}"
    update_env "EMBEDDING_MODEL_PATH" "/models/multilingual-e5-large"
    update_env "EMBEDDING_DIM" "1024"
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
        log "Если забыли: docker compose exec backend python scripts/manage.py reset-admin"
    else
        log "Создание администратора..."
        exec_backend reset-admin
    fi
}

# --- Установка ---

containers_exist() {
    [ -n "$(dc ps -a --quiet 2>/dev/null || true)" ]
}

full_install() {
    prepare
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
        echo ""
        echo "Возможные причины:"
        echo "  - .env пересоздали вручную, а том pgdata остался"
        echo "  - выполняли 'docker compose down -v', но .env сохранили"
        echo ""
        echo "Что делать:"
        echo "  1) Если данные не нужны — выберите 'Полная переустановка (сброс БД)'"
        echo "  2) Если данные нужны — восстановите пароль в БД:"
        echo "     docker compose exec postgres psql -U $(db_user) -d postgres \\"
        echo "       -c \"ALTER USER $(db_user) WITH PASSWORD 'ПАРОЛЬ_ИЗ_ENV';\""
        echo "     затем перезапустите: ./install.sh"
        return 1
    fi
    log "Пароль БД в порядке"

    log "Скачивание моделей (пропускает уже скачанные)..."
    download_models

    log "Инициализация схемы БД (idempotent)..."
    exec_backend init-db

    ensure_admin

    log "Установка завершена."
    echo ""
    echo "Frontend: http://localhost:3000"
    echo "API:      http://localhost:8000/docs"
}

full_reinstall() {
    prepare
    warn "Это УДАЛИТ базу данных, чаты, документы и пересоздаст .env."
    read -r -p "Продолжить? (y/N): " ok
    [ "$ok" = "y" ] || { log "Отменено"; return 1; }

    if containers_exist; then
        dc down -v --remove-orphans || true
    else
        # На случай, если том остался от прошлой установки
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
    echo ""
    echo "Frontend: http://localhost:3000"
    echo "API:      http://localhost:8000/docs"
    echo "Пароль администратора — см. вывод reset-admin выше."
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
        echo "  5) set-llm              0) Назад"
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
            0) return;;
        esac
    done
}

while true; do
    echo ""
    echo "=================================================="
    echo "  ConturAI"
    echo "=================================================="
    echo "  1) Установка / обновление (данные сохраняются)"
    echo "  2) Полная переустановка (сброс БД, новый пароль)"
    echo "  3) Управление контейнерами"
    echo "  4) Команды manage.py"
    echo "  5) Выход"
    read -r -p "Номер [1]: " choice
    case "${choice:-1}" in
        1) full_install;;
        2) full_reinstall;;
        3) containers_menu;;
        4) manage_menu;;
        5) exit 0;;
        *) err "Неверный выбор";;
    esac
done