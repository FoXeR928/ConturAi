@echo off
chcp 65001 >nul
cd /d "%~dp0"

docker info >nul 2>&1
if errorlevel 1 (
    echo ==================================================
    echo   [ERROR] Docker не установлен или не запущен!
    echo ==================================================
    echo Пожалуйста, скачайте и установите Docker Desktop:
    echo https://www.docker.com/products/docker-desktop/
    pause & exit /b 1
)

echo [INFO] Запуск установщика ConturAI...

:: Сохраняем текущий путь хоста в переменную
set "HOST_PROJECT_DIR=%cd%"

:: Монтируем папку проекта в /app внутри контейнера,
:: задаём рабочую директорию /app и передаём хостовый путь через переменную окружения
docker run --rm -it ^
    -v "%cd%:/app" ^
    -v "//./pipe/docker_engine://./pipe/docker_engine" ^
    -w /app ^
    -e HOST_PROJECT_DIR="%HOST_PROJECT_DIR%" ^
    python:3.12-slim sh -c "apt-get update && apt-get install -y docker.io docker-compose && python install.py"

pause