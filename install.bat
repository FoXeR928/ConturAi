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
set "DOWNLOAD=docker compose run --rm --no-deps -v ".\models:/models" -e HF_HUB_OFFLINE=0 -e TRANSFORMERS_OFFLINE=0 -e HF_DATASETS_OFFLINE=0 backend python scripts/manage.py download-models"

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
if not exist backend\pyproject.toml (
    echo [ERROR] Не найден backend\pyproject.toml
    exit /b 1
)
echo [INFO] Пересборка uv.lock...

for %%F in (backend\uv.lock) do set "OLD_TIME=%%~tF"

docker run --rm -v "%cd%\backend:/app" -w /app -e UV_PROJECT_ENVIRONMENT=/tmp/uv-venv python:3.12-slim sh -c "pip install --quiet uv==0.5.11 && uv lock"
if errorlevel 1 (
    echo [ERROR] Не удалось пересобрать uv.lock
    pause & exit /b 1
)

for %%F in (backend\uv.lock) do set "NEW_TIME=%%~tF"
if "!OLD_TIME!"=="!NEW_TIME!" (
    echo [WARN] uv.lock не изменился
)
echo [OK] uv.lock готов
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

if "%PLAT%"=="nvidia" (
    set "IDX=https://download.pytorch.org/whl/cu121"
    set "IMAGE=vllm/vllm-openai:latest"
)
if "%PLAT%"=="amd" (
    set "IDX=https://download.pytorch.org/whl/rocm6.1"
    set "IMAGE=rocm/vllm:latest"
)
if "%PLAT%"=="cpu" (
    set "IDX=https://download.pytorch.org/whl/cpu"
    set "IMAGE=vllm/vllm-openai-cpu:latest"
)

powershell -NoProfile -Command ^
  "$k=@{'PYTORCH_INDEX'='!IDX!';'VLLM_IMAGE'='!IMAGE!'};" ^
  "$c=Get-Content -Raw .env;" ^
  "foreach($key in $k.Keys){ if($c -match \"$key=\"){ $c = $c -replace \"$key=.*\", \"$key=$($k[$key])\" } else { if(-not $c.EndsWith(\"`n\")){$c += \"`n\"}; $c += \"$key=$($k[$key])\" } };" ^
  "Set-Content -NoNewline -Encoding UTF8 .env $c;"
exit /b 0

REM ---------- Выбор модели ----------
:pick_model
echo.
echo Выберите модель ИИ ^(влияет на качество и VRAM^):
echo   1^) Qwen2.5-0.5B-Instruct (CPU, слабый ПК)
echo   2^) Qwen2.5-1.5B-Instruct (8-12 ГБ VRAM, RTX 2070)
echo   3^) Qwen2.5-3B-Instruct   (16 ГБ VRAM, AMD 9070)
echo   4^) Qwen2.5-7B-Instruct   (24+ ГБ VRAM, если хватит памяти)
set /p M=[2]: 
if "%M%"=="" set M=2

if "%M%"=="1" (
    set "MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct"
    set "MODEL_FILE=Qwen2.5-0.5B-Instruct"
    set "MAX_LEN=2048"
)
if "%M%"=="2" (
    set "MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct"
    set "MODEL_FILE=Qwen2.5-1.5B-Instruct"
    set "MAX_LEN=2048"
)
if "%M%"=="3" (
    set "MODEL_NAME=Qwen/Qwen2.5-3B-Instruct"
    set "MODEL_FILE=Qwen2.5-3B-Instruct"
    set "MAX_LEN=4096"
)
if "%M%"=="4" (
    set "MODEL_NAME=Qwen/Qwen2.5-7B-Instruct"
    set "MODEL_FILE=Qwen2.5-7B-Instruct"
    set "MAX_LEN=8192"
)

set "MODELS=intfloat/multilingual-e5-large:multilingual-e5-large,BAAI/bge-reranker-v2-m3:bge-reranker-v2-m3,!MODEL_NAME!:!MODEL_FILE!"

powershell -NoProfile -Command ^
  "$k=@{'VLLM_MODEL_PATH'='/models/!MODEL_FILE!';'VLLM_MAX_MODEL_LEN'='!MAX_LEN!';'VLLM_SERVED_NAME'='local-model';'EMBEDDING_MODEL_PATH'='/models/multilingual-e5-large';'EMBEDDING_DIM'='1024';'MODELS_TO_DOWNLOAD'='!MODELS!'};" ^
  "$c=Get-Content -Raw .env;" ^
  "foreach($key in $k.Keys){ if($c -match \"$key=\"){ $c = $c -replace \"$key=.*\", \"$key=$($k[$key])\" } else { if(-not $c.EndsWith(\"`n\")){$c += \"`n\"}; $c += \"$key=$($k[$key])\" } };" ^
  "Set-Content -NoNewline -Encoding UTF8 .env $c;"
exit /b 0

REM ---------- Выбор платформы ----------
:pick_platform
echo.
echo Выберите платформу:
echo   1^) nvidia
echo   2^) amd
echo   3^) cpu
set /p P=[1]: 
if "%P%"=="" set P=1

set "MODE=nvidia"
if "%P%"=="2" set "MODE=amd"
if "%P%"=="3" set "MODE=cpu"

call :setup_env
call :use_platform %MODE%
call :pick_model
exit /b 0

REM ---------- Ожидание БД ----------
:wait_postgres
echo [INFO] Ожидание PostgreSQL...
:wait_loop
docker compose exec -T postgres pg_isready -U conturai_user >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto wait_loop
)
exit /b 0

REM ---------- Установка с нуля ----------
:full_install
echo.
if exist .env goto err_env_exists

call :pick_platform
call :regen_lock

echo [INFO] Сборка и запуск контейнеров...
docker compose down --remove-orphans 2>nul
docker compose up -d --build
if errorlevel 1 goto err_build

call :wait_postgres

docker compose exec -T postgres psql -U conturai_user -d conturai_db -c "SELECT 1" >nul 2>&1
if errorlevel 1 goto err_password

echo [INFO] Скачивание моделей...
call :download_models
%MANAGE% init-db
%MANAGE% reset-admin

echo [OK] Установка завершена.
echo Frontend: http://localhost:3000
pause
exit /b 0

:err_env_exists
echo [ERROR] Файл .env уже существует. 
echo Для чистой установки удалите файл .env и папку data, либо выберите пункт 3.
pause
exit /b 1

:err_build
echo [ERROR] Ошибка сборки контейнеров.
pause
exit /b 1

:err_password
echo [ERROR] Пароль в .env не совпадает с паролем в pgdata.
echo Выберите 3^) Полная переустановка.
pause
exit /b 1

REM ---------- Обновление ----------
:update_install
echo.
if not exist .env goto err_no_env

echo [INFO] Обновление (данные сохраняются)...
call :regen_lock

echo [INFO] Пересборка и перезапуск контейнеров...
docker compose down --remove-orphans 2>nul
docker compose up -d --build
if errorlevel 1 goto err_build

call :wait_postgres

echo [INFO] Применение миграций БД...
%MANAGE% migrate

echo [INFO] Проверка и скачивание моделей...
call :download_models

echo [OK] Обновление успешно завершено.
pause
exit /b 0

:err_no_env
echo [ERROR] Файл .env не найден. Сначала выполните Установку (пункт 1).
pause
exit /b 1

REM ---------- Полная переустановка ----------
:full_reinstall
echo.
echo [WARN] Это удалит БД, чаты, документы и пересоздаст .env.
set /p OK=Продолжить? (y/N): 
if /i not "%OK%"=="y" exit /b 0

docker compose down -v --remove-orphans 2>nul
docker volume rm conturai_pgdata conturai_app_data 2>nul
del /q .env 2>nul

call :pick_platform
call :regen_lock

docker compose up -d --build
call :wait_postgres

call :download_models
%MANAGE% init-db
%MANAGE% reset-admin
echo [OK] Полная переустановка завершена.
pause
exit /b 0

REM ---------- Обертка для скачивания ----------
:download_models
%DOWLOAD%
exit /b 0

REM ---------- Меню manage.py ----------
:manage_menu
echo.
echo ==================================================
echo   Управление БД и моделями
echo ==================================================
echo   1^) init-db (Создать таблицы)
echo   2^) reset-admin (Сбросить пароль админа)
echo   3^) download-models (Скачать модели)
echo   4^) reembed (Переиндексация RAG)
echo   5^) backup (Резервная копия)
echo   6^) migrate (Применить миграции)
echo   0^) Назад
set /p M_ACT=[1]: 
if "%M_ACT%"=="" set M_ACT=1

if "%M_ACT%"=="1" %MANAGE% init-db
if "%M_ACT%"=="2" %MANAGE% reset-admin
if "%M_ACT%"=="3" call :download_models
if "%M_ACT%"=="4" %MANAGE% reembed
if "%M_ACT%"=="5" %MANAGE% backup
if "%M_ACT%"=="6" %MANAGE% migrate
if "%M_ACT%"=="0" goto main_menu
pause
goto manage_menu

REM ---------- Меню ----------
:main_menu
echo.
echo ==================================================
echo   ConturAI
echo ==================================================
echo   1^) Установка (с нуля)
echo   2^) Обновление (сохранить данные)
echo   3^) Полная переустановка (сброс БД)
echo   4^) Запустить контейнеры (up -d)
echo   5^) Управление БД и моделями
echo   6^) Выход
set /p MAIN=[1]: 
if "%MAIN%"=="" set MAIN=1
if "%MAIN%"=="1" call :full_install & goto main_menu
if "%MAIN%"=="2" call :update_install & goto main_menu
if "%MAIN%"=="3" call :full_reinstall & goto main_menu
if "%MAIN%"=="4" ( docker compose up -d & pause & goto main_menu )
if "%MAIN%"=="5" goto manage_menu
if "%MAIN%"=="6" exit /b 0
goto main_menu