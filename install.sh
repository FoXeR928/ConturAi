#!/usr/bin/env bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "=================================================="
echo "  ConturAI - Установщик (WSL/Linux)"
echo "=================================================="

# 1. Проверка Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker не установлен!"
    echo "Убедитесь, что Docker Desktop запущен и включена интеграция с WSL 2."
    echo "https://docs.docker.com/desktop/wsl/"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker не запущен. Запустите Docker Desktop и повторите."
    exit 1
fi

# 2. Проверка Python (нужен для install.py)
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] Python 3 не найден в WSL."
    echo "Установите его командой: sudo apt update && sudo apt install python3"
    exit 1
fi

# 3. Запуск установщика
echo "[INFO] Запуск мастера настройки..."
# Запускаем install.py напрямую через Python в WSL
python3 install.py