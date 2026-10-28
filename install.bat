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

echo [INFO] Подготовка установщика (сборка образа)...
docker build -t conturai-installer -f Dockerfile.installer .

echo [INFO] Запуск установщика ConturAI...

:: Монтируем текущую папку в /app, а хостовый путь передаем через переменную
docker run --rm -it ^
    -v "%cd%:/app" ^
    -v "//./pipe/docker_engine://./pipe/docker_engine" ^
    -w /app ^
    -e HOST_PROJECT_DIR="%cd%" ^
    conturai-installer python install.py

pause