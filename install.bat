@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker не запущен. Откройте Docker Desktop.
    pause & exit /b 1
)

set "MANAGE=docker compose exec -T backend python scripts/manage.py"
set "DOWNLOAD=docker compose run --rm --no-deps -e HF_HUB_OFFLINE=0 -e TRANSFORMERS_OFFLINE=0 backend python scripts/manage.py download-models"

goto main_menu

REM ---------- .env ----------
:setup_env
if exist .env (
    echo [INFO] .env уже существует — пароль сохранён
    exit /b 0
)
echo [INFO] Создаю .env...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$pass = -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_});" ^
  "$c = Get-Content -Raw .env.example;" ^
  "$c = $c -replace 'DB_USER=.*', 'DB_USER=conturai_user';" ^
  "$c = $c -replace 'DB_PASSWORD=.*', ('DB_PASSWORD=' + $pass);" ^
  "Set-Content -NoNewline -Encoding UTF8 .env $c;"
exit /b 0

:regen_lock
echo [INFO] Пересборка uv.lock...
docker run --rm -v "%cd%\backend:/app" -w /app -e UV_PROJECT_ENVIRONMENT=/tmp/uv-venv python:3.12-slim sh -c "pip install --quiet uv==0.5.11 && uv lock"
if errorlevel 1 (
    echo [ERROR] Не удалось пересобрать uv.lock
    pause & exit /b 1
)
exit /b 0

REM ---------- Синхронизация платформы ----------
:use_platform
set "PLAT=%~1"
set "SRC=templates\docker-compose.%PLAT%.yml"
if not exist "%SRC%" (
    echo [ERROR] Не найден %SRC%
    exit /b 1
)
copy /Y "%SRC%" docker-compose.yml >nul

REM Задаем модели в зависимости от платформы
if "%PLAT%"=="nvidia" (
    set "IDX=https://download.pytorch.org/whl/cu121"
    set "MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct"
    set "MODEL_FILE=Qwen2.5-1.5B-Instruct"
)
if "%PLAT%"=="amd" (
    set "IDX=https://download.pytorch.org/whl/rocm6.1"
    set "MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct"
    set "MODEL_FILE=Qwen2.5-1.5B-Instruct"
)
if "%PLAT%"=="cpu" (
    set "IDX=https://download.pytorch.org/whl/cpu"
    set "MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct"
    set "MODEL_FILE=Qwen2.5-0.5B-Instruct"
)

set "MODELS=intfloat/multilingual-e5-large:multilingual-e5-large,!MODEL_NAME!:!MODEL_FILE!"

REM Обновляем .env через PowerShell (надежнее, чем sed в Windows)
powershell -NoProfile -Command ^
  "$k=@{'PYTORCH_INDEX'='!IDX!';'VLLM_MODEL_PATH'='/models/!MODEL_FILE!';'VLLM_SERVED_NAME'='local-model';'EMBEDDING_MODEL_PATH'='/models/multilingual-e5-large';'EMBEDDING_DIM'='1024';'MODELS_TO_DOWNLOAD'='!MODELS!'};" ^
  "$c=Get-Content -Raw .env;" ^
  "foreach($key in $k.Keys){ if($c -match \"$key=\"){ $c = $c -replace \"$key=.*\", \"$key=$($k[$key])\" } else { if(-not $c.EndsWith(\"`n\")){$c += \"`n\"}; $c += \"$key=$($k[$key])\" } };" ^
  "Set-Content -NoNewline -Encoding UTF8 .env $c;"
exit /b 0

:pick_platform
echo.
echo Выберите платформу:
echo   1^) nvidia (RTX 2070 — тест)
echo   2^) amd    (ROCm — прод)
echo   3^) cpu
set /p P=[1]: 
if "%P%"=="" set P=1
if "%P%"=="1" set MODE=nvidia
if "%P%"=="2" set MODE=amd
if "%P%"=="3" set MODE=cpu
if not defined MODE ( echo [ERROR] Неверный выбор & exit /b 1 )
call :setup_env
call :use_platform !MODE!
exit /b 0

REM ---------- Полная переустановка ----------
:full_reinstall
echo.
echo [WARN] Это удалит БД, чаты, документы и пересоздаст .env.
set /p OK=Продолжить? (y/N): 
if /i not "%OK%"=="y" exit /b 0

echo [INFO] Остановка контейнеров и удаление томов...
docker compose down -v --remove-orphans 2>nul
docker volume rm conturai_pgdata conturai_app_data 2>nul
del /q .env 2>nul

call :pick_platform
if errorlevel 1 pause & exit /b 1
call :regen_lock

echo [INFO] Сборка и запуск контейнеров...
docker compose up -d --build
timeout /t 10 /nobreak >nul

echo [INFO] Скачивание моделей...
%DOWNLOAD%
if errorlevel 1 ( pause & exit /b 1 )

echo [INFO] Инициализация БД...
%MANAGE% init-db

echo [INFO] Создание администратора...
%MANAGE% reset-admin

echo.
echo [OK] Полная переустановка завершена. Пароль admin — в логе reset-admin выше.
pause
exit /b 0

REM ---------- Меню ----------
:main_menu
echo.
echo ==================================================
echo   ConturAI
echo ==================================================
echo   1^) Установка / обновление (данные сохраняются)
echo   2^) Полная переустановка (сброс БД, новый пароль)
echo   3^) Управление контейнерами (up/down/restart)
echo   4^) Выход
set /p MAIN=[1]: 
if "%MAIN%"=="" set MAIN=1
if "%MAIN%"=="1" call :full_install & goto main_menu
if "%MAIN%"=="2" call :full_reinstall & goto main_menu
if "%MAIN%"=="3" (
    docker compose up -d
    echo Запущено.
    pause
    goto main_menu
)
if "%MAIN%"=="4" exit /b 0
goto main_menu