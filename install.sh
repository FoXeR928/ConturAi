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
        macos)   brew install $pkgs;;
        *) err "Не знаю как установить: $pkgs"; exit 1;;
    esac
}

ensure_python() {
    if has python3 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' 2>/dev/null; then
        PYTHON=python3
        log "Python $(python3 -V 2>&1) найден"
        return
    fi
    log "Устанавливаю Python 3..."
    case "$OS" in
        debian) pkg_install python3 python3-venv;;
        rhel)   pkg_install python3;;
        arch)   pkg_install python;;
        suse)   pkg_install python3;;
        macos)  has brew || { err "Нужен Homebrew: https://brew.sh"; exit 1; }; brew install python@3.12;;
    esac
    PYTHON=python3
    python3 -V || { err "Python не установился."; exit 1; }
}

ensure_curl() { has curl || { log "Устанавливаю curl..."; pkg_install curl; }; }
ensure_git()  { has git  || { log "Устанавливаю git...";  pkg_install git;  }; }

ensure_docker_running() {
    if docker info >/dev/null 2>&1; then DOCKER="docker"; log "Docker запущен"; return; fi
    if [ -n "$SUDO" ] && $SUDO docker info >/dev/null 2>&1; then DOCKER="$SUDO docker"; log "Docker запущен (sudo)"; return; fi

    log "Пытаюсь запустить Docker..."
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
    case "$OS" in macos) err "Откройте Docker Desktop вручную.";; *) err "Проверьте: sudo systemctl status docker";; esac
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
        warn "Нет docker compose — устанавливаю..."
        case "$OS" in
            debian|rhel) pkg_install docker-compose-plugin 2>/dev/null || pkg_install docker-compose;;
            arch|suse)   pkg_install docker-compose;;
            macos)       brew install docker-compose;;
        esac
    fi
    ensure_docker_running
}

PREPARE_DONE=0
prepare_env() {
    [ "$PREPARE_DONE" -eq 1 ] && return
    ensure_curl; ensure_python; ensure_git; ensure_docker
    PREPARE_DONE=1
}

DOCKER="docker"
dc() { $DOCKER compose "$@"; }
run_no_deps() { dc run --rm --no-deps backend python scripts/manage.py "$@"; }
exec_backend() { dc exec -T backend python scripts/manage.py "$@"; }
env_cmd() { $PYTHON scripts/env_tool.py "$@"; }

pick_platform() {
    local auto="cpu"
    if has nvidia-smi && nvidia-smi >/dev/null 2>&1; then auto="nvidia"
    elif [ -e /dev/kfd ] || (has rocm-smi && rocm-smi >/dev/null 2>&1); then auto="amd"
    fi

    echo ""
    echo "Обнаружено: $auto"
    echo "Выберите платформу:"
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
    env_cmd setup-env
    env_cmd use-platform "$MODE"
}

full_install() {
    prepare_env
    pick_platform || return 1
    docker_works() || return 1
    log "Сборка backend..."
    dc build backend
    log "Скачивание моделей..."
    run_no_deps download-models
    log "Запуск контейнеров..."
    dc up -d --build
    log "Ожидание PostgreSQL..."
    for _ in $(seq 1 40); do
        dc exec -T postgres pg_isready -U "$(grep '^DB_USER=' .env | cut -d= -f2)" >/dev/null 2>&1 && break
        sleep 2
    done
    log "Инициализация БД..."
    exec_backend init-db
    log "Создание администратора..."
    exec_backend reset-admin
    log "Готово."
}

docker_works() {
    if docker info >/dev/null 2>&1; then DOCKER="docker"; return 0; fi
    if [ -n "$SUDO" ] && $SUDO docker info >/dev/null 2>&1; then DOCKER="$SUDO docker"; return 0; fi
    ensure_docker_running
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
    prepare_env
    while true; do
        echo ""
        echo "--- manage.py ---"
        echo "  1) setup-env       2) use-platform nvidia"
        echo "  3) use-platform amd   4) use-platform cpu"
        echo "  5) use-platform dev   6) download-models"
        echo "  7) download-models --only   8) init-db"
        echo "  9) reset-admin    10) set-llm   0) Назад"
        read -r -p "Номер: " m
        case "$m" in
            1) env_cmd setup-env;;
            2) env_cmd use-platform nvidia;;
            3) env_cmd use-platform amd;;
            4) env_cmd use-platform cpu;;
            5) env_cmd use-platform dev;;
            6) run_no_deps download-models;;
            7) read -r -p "repo:name,repo:name: " only; run_no_deps download-models --only "$only";;
            8) exec_backend init-db;;
            9) exec_backend reset-admin;;
            10)
                read -r -p "model: " model
                read -r -p "temperature: " temp
                read -r -p "max-tokens: " mt
                args=""
                [ -n "$model" ] && args+=" --model $model"
                [ -n "$temp" ]  && args+=" --temperature $temp"
                [ -n "$mt" ]    && args+=" --max-tokens $mt"
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
    echo "  1) Полная установка"
    echo "  2) Управление контейнерами"
    echo "  3) Команды manage.py"
    echo "  4) Выход"
    read -r -p "Номер [1]: " choice
    case "${choice:-1}" in
        1) full_install;;
        2) prepare_env; containers_menu;;
        3) prepare_env; manage_menu;;
        4) exit 0;;
        *) err "Неверный выбор";;
    esac
done