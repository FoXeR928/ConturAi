@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==================================================
echo   ConturAI - Установка
echo ==================================================
echo.
echo Выберите режим установки:
echo   1^) NVIDIA GPU ^(CUDA^)           - полный стек
echo   2^) AMD GPU ^(ROCm^)              - полный стек
echo   3^) CPU ^(8+ ГБ ОЗУ^)             - полный стек
echo   4^) Слабый ПК ^(4-8 ГБ ОЗУ, CPU^) - легкие модели
echo   5^) Только backend ^(без vLLM^)   - API + БД
echo   6^) Только frontend               - интерфейс
echo.
set /p PLATFORM="Введите номер [1]: "
if "%PLATFORM%"=="" set PLATFORM=1
set "PLATFORM=%PLATFORM: =%"

if "%PLATFORM%"=="1" ( set MODE=nvidia & set COMPOSE_BASE=-f docker-compose.yml )
if "%PLATFORM%"=="2" ( set MODE=amd & set COMPOSE_BASE=-f docker-compose.yml -f docker-compose.amd.yml )
if "%PLATFORM%"=="3" ( set MODE=cpu & set COMPOSE_BASE=-f docker-compose.yml -f docker-compose.cpu.yml )
if "%PLATFORM%"=="4" ( set MODE=dev & set COMPOSE_BASE=-f docker-compose.dev.yml )
if "%PLATFORM%"=="5" ( set MODE=backend-only & set COMPOSE_BASE=-f docker-compose.yml -f docker-compose.cpu.yml )
if "%PLATFORM%"=="6" ( set MODE=frontend-only & set COMPOSE_BASE=-f docker-compose.yml )

if not defined MODE (
    echo [ERROR] Неверный выбор.
    exit /b 1
)

echo.
echo [INFO] Режим: %MODE%
echo.

REM --- Проверки ---
docker --version >nul 2>&1
if errorlevel 1 ( echo [ERROR] Docker не найден. & exit /b 1 )
docker compose version >nul 2>&1
if errorlevel 1 ( echo [ERROR] Docker Compose не найден. & exit /b 1 )
python --version >nul 2>&1
if errorlevel 1 ( echo [ERROR] python не найден. & exit /b 1 )

REM --- 1. .env ---
if not exist .env (
    echo [INFO] Генерация .env...
    if exist scripts\generate_env.py (
        python scripts\generate_env.py
    ) else if exist backend\scripts\generate_env.py (
        python backend\scripts\generate_env.py
    ) else (
        echo [ERROR] generate_env.py не найден.
        exit /b 1
    )
    if errorlevel 1 exit /b 1
) else (
    echo [OK] .env уже существует.
)

REM --- 2. Значения по умолчанию ---
set "PYTORCH_INDEX=https://download.pytorch.org/whl/cpu"
set "LLM_MODEL=Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
set "EMB_MODEL=intfloat/multilingual-e5-large:multilingual-e5-large"
set "EMB_PATH=/models/multilingual-e5-large"
set "EMB_DIM=1024"

if "%MODE%"=="nvidia" set "PYTORCH_INDEX=https://download.pytorch.org/whl/cu121"
if "%MODE%"=="amd"    set "PYTORCH_INDEX=https://download.pytorch.org/whl/rocm6.1"

if "%MODE%"=="dev" (
    set "LLM_MODEL=Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
    set "EMB_MODEL=ibm-granite/granite-embedding-97m-multilingual-r2:granite-embedding-97m-multilingual-r2"
    set "EMB_PATH=/models/granite-embedding-97m-multilingual-r2"
    set "EMB_DIM=384"
)

set "MODELS_TO_DOWNLOAD=%LLM_MODEL%,%EMB_MODEL%"

echo [INFO] PYTORCH_INDEX      = %PYTORCH_INDEX%
echo [INFO] EMBEDDING_MODEL_PATH = %EMB_PATH%
echo [INFO] EMBEDDING_DIM      = %EMB_DIM%
echo [INFO] MODELS_TO_DOWNLOAD = %MODELS_TO_DOWNLOAD%

REM --- 3. Обновление .env через PS-скрипт ---
(
    echo $ErrorActionPreference = 'Stop'
    echo $path = '.env'
    echo $content = Get-Content -Raw -Encoding UTF8 $path
    echo function Set-Key($k, $v) {
    echo   if ($script:content -match "(?m)^$k=") {
    echo     $script:content = [regex]::Replace($script:content, "(?m)^$k=.*", "$k=$v")
    echo   } else {
    echo     if (-not $script:content.EndsWith("`n")) { $script:content += "`n" }
    echo     $script:content += "$k=$v`n"
    echo   }
    echo }
    echo Set-Key 'PYTORCH_INDEX' '%PYTORCH_INDEX%'
    echo Set-Key 'EMBEDDING_MODEL_PATH' '%EMB_PATH%'
    echo Set-Key 'EMBEDDING_DIM' '%EMB_DIM%'
    echo Set-Key 'MODELS_TO_DOWNLOAD' '%MODELS_TO_DOWNLOAD%'
    echo Set-Content -NoNewline -Encoding UTF8 $path $content
) > .env_upd.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File .env_upd.ps1
if errorlevel 1 (
    echo [ERROR] Не удалось обновить .env через PowerShell.
    del .env_upd.ps1 >nul 2>&1
    exit /b 1
)
del .env_upd.ps1 >nul 2>&1

echo.
echo [OK] .env обновлён. Текущие значения:
findstr /B /C:"PYTORCH_INDEX=" /C:"EMBEDDING_MODEL_PATH=" /C:"EMBEDDING_DIM=" /C:"MODELS_TO_DOWNLOAD=" .env

REM --- 4. Скачивание моделей ---
if not "%MODE%"=="frontend-only" if not "%MODE%"=="backend-only" (
    echo.
    echo [INFO] Скачивание моделей ^(может занять время^)...
    docker compose %COMPOSE_BASE% run --rm --no-deps backend python scripts/manage.py download-models
    if errorlevel 1 ( echo [ERROR] Не удалось скачать модели. & exit /b 1 )
    echo [OK] Модели скачаны.
)

REM --- 5. Запуск ---
echo.
echo [INFO] Запуск контейнеров...
if "%MODE%"=="backend-only" (
    docker compose %COMPOSE_BASE% up -d --build postgres backend
) else if "%MODE%"=="frontend-only" (
    docker compose %COMPOSE_BASE% up -d --build frontend
) else (
    docker compose %COMPOSE_BASE% up -d --build
)
if errorlevel 1 ( echo [ERROR] Не удалось запустить контейнеры. & exit /b 1 )

REM --- 6. Инициализация БД ---
if not "%MODE%"=="frontend-only" (
    echo.
    echo [INFO] Ожидание PostgreSQL...
    for /l %%i in (1,1,40) do (
        docker compose %COMPOSE_BASE% exec -T postgres pg_isready -U conturai_user >nul 2>&1
        if not errorlevel 1 goto db_ready
        timeout /t 2 /nobreak >nul
    )
    echo [ERROR] PostgreSQL не запустился вовремя.
    exit /b 1
    :db_ready
    echo [OK] PostgreSQL готов.

    echo [INFO] Инициализация БД...
    docker compose %COMPOSE_BASE% exec -T backend python scripts/manage.py init-db
    if errorlevel 1 exit /b 1

    echo [INFO] Создание администратора...
    docker compose %COMPOSE_BASE% exec -T backend python scripts/manage.py reset-admin
    if errorlevel 1 exit /b 1
)

REM --- 7. Итог ---
echo.
echo ==================================================
echo   Установка завершена ^(%MODE%^)
echo ==================================================
if "%MODE%"=="frontend-only" ( echo Frontend: http://localhost:3000 )
if "%MODE%"=="backend-only" (
    echo API:      http://localhost:8000/docs
    echo Status:   http://localhost:8000/status
)
if not "%MODE%"=="frontend-only" if not "%MODE%"=="backend-only" (
    echo Frontend: http://localhost:3000
    echo API:      http://localhost:8000/docs
    echo Status:   http://localhost:8000/status
    echo vLLM:     http://localhost:8080/v1
)
echo.
echo Пароль администратора — см. вывод reset-admin выше.
echo.

endlocal