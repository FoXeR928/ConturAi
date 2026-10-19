@echo off
setlocal enabledelayedexpansion

set MODE=%1
if "%MODE%"=="" set MODE=full

echo ==================================================
echo   ConturAI - Установка (режим: %MODE%)
echo ==================================================

docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker не найден.
    exit /b 1
)

REM --- Генерация .env ---
if not exist .env (
    python scripts\generate_env.py
    if errorlevel 1 (
        echo [ERROR] Не удалось создать .env. Убедитесь, что Python установлен.
        exit /b 1
    )
) else (
    echo [OK] Файл .env уже существует.
)

REM --- Маршрутизация режимов ---
if /I "%MODE%"=="full" goto :full
if /I "%MODE%"=="backend" goto :backend
if /I "%MODE%"=="test" goto :backend
if /I "%MODE%"=="frontend" goto :frontend

echo [ERROR] Неизвестный режим: %MODE%
echo Доступные режимы: full, backend, frontend, test
exit /b 1

REM --- Режим FULL ---
:full
call :run_backend
call :run_frontend
goto :done

REM --- Режим FRONTEND ---
:frontend
echo [INFO] Сборка и запуск Фронтенда...
docker compose up -d --build frontend
goto :done

REM --- Режим BACKEND / TEST ---
:backend
call :run_backend
goto :done

REM --- Функция запуска бэкенда ---
:run_backend
echo [INFO] Сборка и запуск БД, vLLM и Бэкенда...
docker compose up -d --build postgres vllm backend

echo [INFO] Ожидание PostgreSQL...
timeout /t 10 /nobreak >nul

echo [INFO] Инициализация БД...
docker compose exec -T backend python scripts/manage.py init-db
if errorlevel 1 exit /b 1

echo [INFO] Создание администратора...
docker compose exec -T backend python scripts/manage.py reset-admin
if errorlevel 1 exit /b 1
exit /b 0

REM --- Завершение ---
:done
echo ==================================================
echo   Установка завершена (режим: %MODE%)
echo ==================================================
if /I "%MODE%"=="full" (
    echo Frontend: http://localhost:3000
    echo API:      http://localhost:8000/docs
    echo Status:   http://localhost:8000/status
)
if /I "%MODE%"=="backend" (
    echo API:      http://localhost:8000/docs
    echo Status:   http://localhost:8000/status
)
if /I "%MODE%"=="test" (
    echo API:      http://localhost:8000/docs
    echo Status:   http://localhost:8000/status
)
if /I "%MODE%"=="frontend" (
    echo Frontend: http://localhost:3000
)
echo ==================================================

endlocal