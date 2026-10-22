#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

G="\033[0;32m"; R="\033[0;31m"; Y="\033[1;33m"; N="\033[0m"
log()  { echo -e "${G}[INFO]${N}  $*"; }
warn() { echo -e "${Y}[WARN]${N}  $*"; }
err()  { echo -e "${R}[ERROR]${N} $*" >&2; }

if [ "$EUID" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi
has() { command -v "$1" >/dev/null 2>&1; }

detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then echo "macos"; return; fi
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "$ID" in
            ubuntu|debian|linuxmint) echo "debian";;
            fedora|rhel|centos|rocky|almalinux) echo "rhel";;
            arch|manjaro) echo "arch";;
            opensuse*|suse) echo "suse";;
            *) echo "linux:other";;
        esac
    else
        echo "linux:other"
    fi
}
OS=$(detect_os)
log "OS: $OS"

pkg_install() {
    local pkgs="$*"
    case "$OS" in
        debian)  $SUDO apt-get update -y && DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y $pkgs;;
        rhel)    $SUDO dnf install -y $pkgs 2>/dev/null || $SUDO yum install -y $pkgs;;
        arch)    $SUDO pacman -Sy --noconfirm $pkgs;;
        suse)    $SUDO zypper -n install $pkgs;;
        macos)   has brew || { err "Нужен Homebrew: https://brew.sh"; exit 1; }; brew install $pkgs;;
        *) err "Не знаю как установить: $pkgs"; exit 1;;
    esac
}

ensure_curl() { has curl || { log "Устанавливаю curl..."; pkg_install curl; }; }
ensure_git()  { has git  || { log "Устанавливаю git...";  pkg_install git;  }; }

ensure_docker_running() {
    if docker info >/dev/null 2>&1; then DOCKER="docker"; log "Docker запущен"; return; fi
    if [ -n "$SUDO" ] && $SUDO docker info >/dev/null 2>&1; then DOCKER="$SUDO docker"; log "Docker запущен (sudo)"; return; fi

    log "Запускаю Docker..."
    case "$OS" in
        macos) open -a Docker 2>/dev/null || true;;
        *)
            if has systemctl; then $SUDO systemctl enable --now docker 2>/dev/null || $SUDO systemctl start docker 2>/dev/null || true
            elif has service; then $SUDO service docker start 2>/dev/null || true
            fi;;
    esac
    for _ in $(seq 1 30); do
        if docker info >/dev/null 2>&1; then DOCKER="docker"; log "Docker готов"; return; fi
        if [ -n "$SUDO" ] && $SUDO docker info >/dev/null 2>&1; then DOCKER="$SUDO docker"; log "Docker готов (sudo)"; return; fi
        sleep 2
    done
    err "Docker не запустился за 60 сек."
    return 1
}

ensure_docker() {
    if ! has docker; then
        log "Устанавливаю Docker..."
        case "$OS" in
            macos) has brew || { err "Нужен Homebrew или Docker Desktop."; exit 1; }; brew install --cask docker;;
            *) ensure_curl; curl -fsSL https://get.docker.com | $SUDO sh; [ -n "$SUDO" ] && $SUDO usermod -aG docker "$USER" || true;;
        esac
    fi
    if ! docker compose version >/dev/null 2>&1; then
        warn "Нет docker compose — ставлю..."
        case "$OS" in
            debian|rhel) pkg_install docker-compose-plugin 2>/dev/null || pkg_install docker-compose;;
            arch|suse)   pkg_install docker-compose;;
            macos)       brew install docker-compose;;
        esac
    fi
    ensure_docker_running
}

PREPARE_DONE=0
prepare() {
    [ "$PREPARE_DONE" -eq 1 ] && return
    ensure_curl; ensure_git; ensure_docker
    PREPARE_DONE=1
}

DOCKER="docker"
docker_works() {
    if docker info >/dev/null 2>&1; then DOCKER="docker"; return 0; fi
    if [ -n "$SUDO" ] && $SUDO docker info >/dev/null 2>&1; then DOCKER="$SUDO docker"; return 0; fi
    ensure_docker_running
}
dc() { $DOCKER compose "$@"; }
exec_backend() { dc exec -T backend python scripts/manage.py "$@"; }

download_models() {
    # скачивание в одноразовом контейнере с интернетом
    dc run --rm --no-deps \
        -e HF_HUB_OFFLINE=0 \
        -e TRANSFORMERS_OFFLINE=0 \
        -e HF_DATASETS_OFFLINE=0 \
        backend python scripts/manage.py download-models "$@"
}

# ---------- .env + compose generation (без Python) ----------
gen_password() {
    # 32 буквенно-цифровых символа через /dev/urandom
    LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32
}

setup_env() {
    if [ -f .env ]; then
        log ".env уже существует — пропускаю"
        return
    fi
    if [ ! -f .env.example ]; then
        err "Не найден .env.example"
        exit 1
    fi
    log "Создаю .env (пароль генерируется автоматически)"
    local db_user="conturai_user"
    local db_pass
    db_pass=$(gen_password)
    sed -e "s|^DB_USER=.*|DB_USER=${db_user}|" \
        -e "s|^DB_PASSWORD=.*|DB_PASSWORD=${db_pass}|" \
        .env.example > .env
    log "Пользователь БД: $db_user"
    log "Пароль БД:       $db_pass"
}

use_platform() {
    local platform="$1"
    local src="templates/docker-compose.${platform}.yml"
    if [ ! -f "$src" ]; then
        err "Не найден шаблон $src"
        exit 1
    fi
    cp "$src" docker-compose.yml
    log "docker-compose.yml перезаписан ($platform)"

    # Платформенные параметры в .env
    local idx dtype kvc max_len vllm_mem pg_mem be_mem fe_mem emb_path emb_dim models
    case "$platform" in
        nvidia)
            idx="https://download.pytorch.org/whl/cu121"
            dtype="auto"; kvc=""; max_len="4096"; vllm_mem="12g"
            pg_mem="1g"; be_mem="2g"; fe_mem="256m"
            emb_path="/models/multilingual-e5-large"; emb_dim="1024"
            models="intfloat/multilingual-e5-large:multilingual-e5-large,Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
            ;;
        amd)
            idx="https://download.pytorch.org/whl/rocm6.1"
            dtype="auto"; kvc=""; max_len="4096"; vllm_mem="12g"
            pg_mem="1g"; be_mem="2g"; fe_mem="256m"
            emb_path="/models/multilingual-e5-large"; emb_dim="1024"
            models="intfloat/multilingual-e5-large:multilingual-e5-large,Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
            ;;
        cpu)
            idx="https://download.pytorch.org/whl/cpu"
            dtype="float32"; kvc="4"; max_len="2048"; vllm_mem="8g"
            pg_mem="1g"; be_mem="2g"; fe_mem="256m"
            emb_path="/models/multilingual-e5-large"; emb_dim="1024"
            models="intfloat/multilingual-e5-large:multilingual-e5-large,Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
            ;;
        dev)
            idx="https://download.pytorch.org/whl/cpu"
            dtype="float32"; kvc="1"; max_len="1024"; vllm_mem="3g"
            pg_mem="1g"; be_mem="1g"; fe_mem="256m"
            emb_path="/models/granite-embedding-97m-multilingual-r2"; emb_dim="384"
            models="ibm-granite/granite-embedding-97m-multilingual-r2:granite-embedding-97m-multilingual-r2,Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
            ;;
        *) err "Неизвестная платформа: $platform"; exit 1;;
    esac

    update_env "PYTORCH_INDEX"          "$idx"
    update_env "VLLM_DTYPE"             "$dtype"
    update_env "VLLM_CPU_KVCACHE_SPACE" "$kvc"
    update_env "VLLM_MAX_MODEL_LEN"     "$max_len"
    update_env "VLLM_MEM_LIMIT"         "$vllm_mem"
    update_env "PG_MEM_LIMIT"           "$pg_mem"
    update_env "BACKEND_MEM_LIMIT"      "$be_mem"
    update_env "FRONTEND_MEM_LIMIT"     "$fe_mem"
    update_env "EMBEDDING_MODEL_PATH"   "$emb_path"
    update_env "EMBEDDING_DIM"          "$emb_dim"
    update_env "MODELS_TO_DOWNLOAD"     "$models"
}

update_env() {
    local key="$1" value="$2"
    if grep -q "^${key}=" .env 2>/dev/null; then
        # macOS sed требует -i '', Linux -i
        if sed --version >/dev/null 2>&1; then
            sed -i "s|^${key}=.*|${key}=${value}|" .env
        else
            sed -i '' "s|^${key}=.*|${key}=${value}|" .env
        fi
    else
        echo "${key}=${value}" >> .env
    fi
}

pick_platform() {
    local auto="cpu"
    if has nvidia-smi && nvidia-smi >/dev/null 2>&1; then auto="nvidia"
    elif [ -e /dev/kfd ] || (has rocm-smi && rocm-smi >/dev/null 2>&1); then auto="amd"
    fi

    echo ""
    echo "Обнаружено GPU: $auto"
    echo "  1) nvidia   2) amd   3) cpu   4) dev"
    read -r -p "Номер [$auto]: " p
    p="${p:-$auto}"
    case "$p" in
        nvidia|1) MODE=nvidia;;
        amd|2)    MODE=amd;;
        cpu|3)    MODE=cpu;;
        dev|4)    MODE=dev;;
        *) err "Неверный выбор"; return 1;;
    esac
    setup_env
    use_platform "$MODE"
}

full_install() {
    prepare
    pick_platform || return 1
    docker_works || return 1
    log "Сборка backend..."
    dc up -d --build
    log "Ожидание PostgreSQL..."
    for _ in $(seq 1 40); do
        dc exec -T postgres pg_isready -U "$(grep '^DB_USER=' .env | cut -d= -f2)" >/dev/null 2>&1 && break
        sleep 2
    done
    log "Скачивание моделей..."
    download_models
    log "Инициализация БД..."
    exec_backend init-db
    log "Создание администратора..."
    exec_backend reset-admin
    log "Установка завершена."
}

containers_menu() {
    docker_works || return
    while true; do
        echo ""
        echo "--- Контейнеры ---"
        echo "  1) up -d   2) stop   3) restart   4) up -d --build"
        echo "  5) down    6) down -v   7) logs -f   8) ps   0) Назад"
        read -r -p "Номер: " c
        case "$c" in
            1) dc up -d;;
            2) dc stop;;
            3) dc restart;;
            4) dc up -d --build;;
            5) dc down;;
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
        echo "--- manage.py (в контейнере) ---"
        echo "  1) init-db"
        echo "  2) reset-admin"
        echo "  3) download-models (пропускает уже скачанные)"
        echo "  4) download-models --force (перекачать всё)"
        echo "  5) download-models --only ..."
        echo "  6) download-models --only ... --force"
        echo "  7) set-llm"
        echo "  8) use-platform nvidia  9) amd  10) cpu  11) dev"
        echo "  0) Назад"
        read -r -p "Номер: " m
        case "$m" in
            1) exec_backend init-db;;
            2) exec_backend reset-admin;;
            3) download_models;;
            4) download_models --force;;
            5) read -r -p "repo:name,repo:name: " only; download_models --only "$only";;
            6) read -r -p "repo:name,repo:name: " only; download_models --only "$only" --force;;
            7)
                read -r -p "model: " model
                read -r -p "temperature: " temp
                read -r -p "max-tokens: " mt
                args=""
                [ -n "$model" ] && args+=" --model $model"
                [ -n "$temp" ]  && args+=" --temperature $temp"
                [ -n "$mt" ]    && args+=" --max-tokens $mt"
                exec_backend set-llm $args
                ;;
            8) setup_env; use_platform nvidia;;
            9) setup_env; use_platform amd;;
            10) setup_env; use_platform cpu;;
            11) setup_env; use_platform dev;;
            0) return;;
        esac
    done
}

update_menu() {
    docker_works || return
    while true; do
        echo ""
        echo "--- Обновление / переустановка ---"
        echo "  1) Пересобрать backend (без кеша)"
        echo "  2) Пересобрать frontend (без кеша)"
        echo "  3) Пересобрать всё (без кеша)"
        echo "  4) Обновить код (git pull) + пересобрать всё"
        echo "  5) Полная переустановка: снести контейнеры/тома, скачать модели, поднять"
        echo "  0) Назад"
        read -r -p "Номер: " u
        case "$u" in
            1) dc build --no-cache backend && dc up -d backend;;
            2) dc build --no-cache frontend && dc up -d frontend;;
            3) dc build --no-cache && dc up -d;;
            4)
                has git || { err "git не установлен"; continue; }
                git pull --ff-only
                dc build --no-cache
                dc up -d
                ;;
            5)
                read -r -p "Удалить тома с БД и данными? (y/N): " ok
                if [ "$ok" = "y" ]; then
                    dc down -v
                else
                    dc down
                fi
                dc up -d --build
                for _ in $(seq 1 40); do
                    dc exec -T postgres pg_isready -U "$(grep '^DB_USER=' .env | cut -d= -f2)" >/dev/null 2>&1 && break
                    sleep 2
                done
                exec_backend download-models --force
                exec_backend init-db
                exec_backend reset-admin
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
    echo "  1) Полная установка"
    echo "  2) Управление контейнерами"
    echo "  3) Команды manage.py (в контейнере)"
    echo "  4) Обновление / переустановка"
    echo "  5) Выход"
    read -r -p "Номер [1]: " choice
    case "${choice:-1}" in
        1) full_install;;
        2) prepare; containers_menu;;
        3) prepare; manage_menu;;
        4) prepare; update_menu;;
        5) exit 0;;
        *) err "Неверный выбор";;
    esac
done