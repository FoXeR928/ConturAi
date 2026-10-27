#!/usr/bin/env bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
PROJECT_DIR="$(pwd)"

if ! command -v docker >/dev/null 2>&1; then
    echo "=================================================="
    echo "  [ERROR] Docker не установлен!"
    echo "=================================================="
    echo "Пожалуйста, установите Docker и Docker Compose v2:"
    echo "https://docs.docker.com/engine/install/"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker установлен, но не запущен. Запустите службу Docker и повторите."
    exit 1
fi

echo "[INFO] Подготовка установщика (сборка образа)..."
# Собираем образ с Python + Docker CLI
docker build -t conturai-installer -f Dockerfile.installer .

echo "[INFO] Запуск установщика ConturAI..."
docker run --rm -it \
    -v "${PROJECT_DIR}:${PROJECT_DIR}" \
    -v "/var/run/docker.sock:/var/run/docker.sock" \
    -w "${PROJECT_DIR}" \
    conturai-installer python install.py