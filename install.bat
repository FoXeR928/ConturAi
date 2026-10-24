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
set "DOWNLOAD=docker compose run --rm --no-deps -v "%cd%\models:/models" -e HF_HUB_OFFLINE=0 -e TRANSFORMERS_OFFLINE=0 backend python scripts/manage.py download-models"

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

REM Запоминаем время модификации до
for %%F in (backend\uv.lock) do set "OLD_TIME=%%~tF"

docker run --rm -v "%cd%\backend:/app" -w /app -e UV_PROJECT_ENVIRONMENT=/tmp/uv-venv python:3.12-slim sh -c "pip install --quiet uv==0.5.11 && uv lock"
if errorlevel 1 (
    echo [ERROR] Не удалось пересобрать uv.lock
    pause & exit /b 1
)

REM Проверяем, что файл обновился
for %%F in (backend\uv.lock) do set "NEW_TIME=%%~tF"
if "!OLD_TIME!"=="!NEW_TIME!" (
    echo [WARN] uv.lock не изменился — возможно, был актуален
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

set "MODELS=intfloat/multilingual-e5-large:multilingual-e5-large,!MODEL_NAME!:!MODEL_FILE!"

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
if "%P%"=="1" set MODE=nvidia
if "%P%"=="2" set MODE=amd
if "%P%"=="3" set MODE=cpu
if not defined MODE ( echo [ERROR] Неверный выбор & exit /b 1 )
call :setup_env
call :use_platform !MODE!
call :pick_model
exit /b 0

REM ---------- Установка / Обновление ----------
:full_install
call :pick_platform
if errorlevel 1 exit /b 1
call :regen_lock

echo [INFO] Сборка и запуск контейнеров...
docker compose down --remove-orphans 2>nul
docker compose up -d --build
if errorlevel 1 ( pause & exit /b 1 )

echo [INFO] Ожидание...
timeout /t 10 /nobreak >nul

docker compose exec -T postgres psql -U conturai_user -d conturai_db -c "SELECT 1" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Пароль в .env не совпадает с паролем в pgdata.
    echo Выберите 2^) Полная переустановка.
    pause & exit /b 1
)

echo [INFO] Скачивание моделей...
%DOWNLOAD%
%MANAGE% init-db

for /f "tokens=*" %%c in ('docker compose exec -T postgres psql -U conturai_user -d conturai_db -tAc "SELECT count(*) FROM users WHERE login='admin'" 2^>nul') do set ADMIN_COUNT=%%c
set "ADMIN_COUNT=%ADMIN_COUNT: =%"
if "%ADMIN_COUNT%"=="" set ADMIN_COUNT=0
if "%ADMIN_COUNT%"=="0" (
    %MANAGE% reset-admin
) else (
    echo [INFO] Администратор уже существует.
)

echo [OK] Установка завершена.
pause
exit /b 0

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
timeout /t 10 /nobreak >nul
%DOWNLOAD%
%MANAGE% init-db
%MANAGE% reset-admin
echo [OK] Полная переустановка завершена.
pause
exit /b 0

REM ---------- Меню ----------
:main_menu
echo.
echo ==================================================
echo   ConturAI
echo ==================================================
echo   1^) Установка / обновление
echo   2^) Полная переустановка
echo   3^) Запустить контейнеры (up -d)
echo   4^) Выход
set /p MAIN=[1]: 
if "%MAIN%"=="" set MAIN=1
if "%MAIN%"=="1" call :full_install & goto main_menu
if "%MAIN%"=="2" call :full_reinstall & goto main_menu
if "%MAIN%"=="3" ( docker compose up -d & pause & goto main_menu )
if "%MAIN%"=="4" exit /b 0
goto main_menu