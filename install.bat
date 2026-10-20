@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==================================================
echo   ConturAI - установка
echo ==================================================
echo.
echo Выберите платформу для запуска vLLM:
echo   1^) NVIDIA GPU ^(CUDA^)
echo   2^) AMD GPU ^(ROCm^)
echo   3^) CPU ^(тест / без GPU^)
echo   4^) Только бэкенд ^(без фронтенда и vLLM^)
echo   5^) Только фронтенд
echo.
set /p PLATFORM="Введите номер [1]: "
if "%PLATFORM%"=="" set PLATFORM=1

if "%PLATFORM%"=="1" set MODE=nvidia
if "%PLATFORM%"=="2" set MODE=amd
if "%PLATFORM%"=="3" set MODE=cpu
if "%PLATFORM%"=="4" set MODE=backend-only
if "%PLATFORM%"=="5" set MODE=frontend-only

if not defined MODE (
    echo [ERROR] Неверный выбор: %PLATFORM%
    exit /b 1
)

echo.
echo [INFO] Выбран режим: %MODE%
echo.

REM --- Проверка Docker ---
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker не найден. Установите Docker Desktop.
    exit /b 1
)
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose не найден. Обновите Docker Desktop.
    exit /b 1
)
echo [OK] Docker и Docker Compose найдены.

REM --- Проверка Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] python не найден. Установите Python 3.11+ и добавьте в PATH.
    exit /b 1
)
echo [OK] Python найден.

REM --- 1. .env ---
if not exist .env (
    echo.
    echo [INFO] Генерация .env с безопасными паролями...
    python scripts\generate_env.py
    if errorlevel 1 (
        echo [ERROR] Не удалось создать .env.
        exit /b 1
    )
) else (
    echo [OK] .env уже существует, используем его.
)

REM --- 2. PYTORCH_INDEX ---
if "%MODE%"=="nvidia" set PYTORCH_INDEX=https://download.pytorch.org/whl/cu121
if "%MODE%"=="amd" set PYTORCH_INDEX=https://download.pytorch.org/whl/rocm6.1
if "%MODE%"=="cpu" set PYTORCH_INDEX=https://download.pytorch.org/whl/cpu
if "%MODE%"=="backend-only" set PYTORCH_INDEX=https://download.pytorch.org/whl/cpu
if "%MODE%"=="frontend-only" set PYTORCH_INDEX=https://download.pytorch.org/whl/cpu

REM Перезаписываем PYTORCH_INDEX в .env через PowerShell (проще, чем findstr)
powershell -NoProfile -Command ^
  "$c = Get-Content -Raw '.env'; if ($c -match 'PYTORCH_INDEX=') { $c = $c -replace 'PYTORCH_INDEX=.*', 'PYTORCH_INDEX=%PYTORCH_INDEX%' } else { $c += \"`nPYTORCH_INDEX=%PYTORCH_INDEX%\" }; Set-Content -NoNewline '.env' $c"
echo [OK] PYTORCH_INDEX=%PYTORCH_INDEX%

REM --- 3. Compose override ---
set COMPOSE_FILES=-f docker-compose.yml
if "%MODE%"=="amd" if exist docker-compose.amd.yml set COMPOSE_FILES=%COMPOSE_FILES% -f docker-compose.amd.yml
if "%MODE%"=="cpu" if exist docker-compose.cpu.yml set COMPOSE_FILES=%COMPOSE_FILES% -f docker-compose.cpu.yml
if "%MODE%"=="backend-only" if exist docker-compose.cpu.yml set COMPOSE_FILES=%COMPOSE_FILES% -f docker-compose.cpu.yml
if "%MODE%"=="frontend-only" if exist docker-compose.cpu.yml set COMPOSE_FILES=%COMPOSE_FILES% -f docker-compose.cpu.yml

REM --- 4. Модели ---
if not "%MODE%"=="frontend-only" (
    echo.
    echo [INFO] Скачивание моделей в .\models (может занять время^)...
    docker compose %COMPOSE_FILES% run --rm backend python scripts/manage.py download-models
    if errorlevel 1 (
        echo [ERROR] Не удалось скачать модели.
        exit /b 1
    )
    echo [OK] Модели скачаны.
)

REM --- 5. Запуск ---
echo.
echo [INFO] Сборка и запуск контейнеров...
if "%MODE%"=="backend-only" (
    docker compose %COMPOSE_FILES% up -d --build postgres backend
) else if "%MODE%"=="frontend-only" (
    docker compose %COMPOSE_FILES% up -d --build frontend
) else (
    docker compose %COMPOSE_FILES% up -d --build
)
if errorlevel 1 (
    echo [ERROR] Не удалось запустить контейнеры.
    exit /b 1
)

REM --- 6. Ожидание БД и инициализация ---
if not "%MODE%"=="frontend-only" (
    echo.
    echo [INFO] Ожидание PostgreSQL...
    for /l %%i in (1,1,30) do (
        docker compose %COMPOSE_FILES% exec -T postgres pg_isready -U conturai_user >nul 2>&1
        if not errorlevel 1 goto db_ready
        timeout /t 2 /nobreak >nul
    )
    echo [ERROR] PostgreSQL не запустился вовремя.
    exit /b 1
    :db_ready
    echo [OK] PostgreSQL готов.

    echo.
    echo [INFO] Инициализация БД, промтов и llm_configs...
    docker compose %COMPOSE_FILES% exec -T backend python scripts/manage.py init-db
    if errorlevel 1 (
        echo [ERROR] Ошибка init-db.
        exit /b 1
    )

    echo.
    echo [INFO] Создание администратора...
    docker compose %COMPOSE_FILES% exec -T backend python scripts/manage.py reset-admin
    if errorlevel 1 (
        echo [ERROR] Ошибка reset-admin.
        exit /b 1
    )
)

REM --- 7. Итог ---
echo.
echo ==================================================
echo   Установка завершена ^(режим: %MODE%^)
echo ==================================================
if "%MODE%"=="frontend-only" (
    echo Frontend: http://localhost:3000
)
if "%MODE%"=="backend-only" (
    echo API:    http://localhost:8000/docs
    echo Status: http://localhost:8000/status
)
if "%MODE%"=="nvidia" (
    echo Frontend: http://localhost:3000
    echo API:      http://localhost:8000/docs
    echo Status:   http://localhost:8000/status
    echo vLLM:     http://localhost:8080/v1
)
if "%MODE%"=="amd" (
    echo Frontend: http://localhost:3000
    echo API:      http://localhost:8000/docs
    echo Status:   http://localhost:8000/status
    echo vLLM:     http://localhost:8080/v1
)
if "%MODE%"=="cpu" (
    echo Frontend: http://localhost:3000
    echo API:      http://localhost:8000/docs
    echo Status:   http://localhost:8000/status
    echo vLLM:     http://localhost:8080/v1 ^(CPU, медленно^)
)
echo.
echo Логин и пароль администратора — см. вывод reset-admin выше.
echo Для изменения параметров LLM без перезапуска:
echo   docker compose exec backend python scripts/manage.py set-llm --model ^<имя^> --temperature 0.5
echo ==================================================

endlocal