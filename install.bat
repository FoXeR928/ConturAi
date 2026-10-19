@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo   ConturAI - установка и запуск
echo ==================================================
echo.

REM --- 1. Проверка Docker ---
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker не найден. Установите Docker Desktop и повторите.
    exit /b 1
)

docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose не найден. Обновите Docker Desktop.
    exit /b 1
)

echo [OK] Docker и Docker Compose найдены.
echo.

REM --- 2. Подготовка .env ---
if not exist .env (
    echo [INFO] Файл .env не найден. Будет создан с автоматическими паролями.
    echo.

    REM Собираем образ бэкенда, чтобы был доступен manage.py setup-env
    echo [INFO] Сборка образа backend...
    docker compose build backend
    if errorlevel 1 (
        echo [ERROR] Не удалось собрать образ backend.
        exit /b 1
    )

    echo [INFO] Генерация .env и случайных паролей...
    docker compose run --rm --no-deps backend python scripts/manage.py setup-env
    if errorlevel 1 (
        echo [ERROR] Не удалось сгенерировать .env.
        exit /b 1
    )
) else (
    echo [OK] Файл .env уже существует, используем его.
)
echo.

REM --- 3. Запуск контейнеров ---
echo [INFO] Сборка и запуск контейнеров...
docker compose up --build -d
if errorlevel 1 (
    echo [ERROR] Не удалось запустить контейнеры.
    exit /b 1
)
echo.

REM --- 4. Ожидание готовности PostgreSQL ---
echo [INFO] Ожидание готовности PostgreSQL...
set /a retries=30
:wait_db
docker compose exec -T postgres pg_isready -U conturai >nul 2>&1
if not errorlevel 1 goto db_ready

set /a retries-=1
if !retries! leq 0 (
    echo [ERROR] PostgreSQL не запустился за отведённое время.
    echo         Проверьте логи: docker compose logs postgres
    exit /b 1
)
timeout /t 2 /nobreak >nul
echo    ожидание... осталось !retries! попыток
goto wait_db

:db_ready
echo [OK] PostgreSQL готов.
echo.

REM --- 5. Инициализация БД ---
echo [INFO] Инициализация схемы базы данных и промтов...
docker compose exec -T backend python scripts/manage.py init-db
if errorlevel 1 (
    echo [ERROR] Ошибка инициализации БД.
    exit /b 1
)
echo.

REM --- 6. Создание администратора ---
echo [INFO] Создание администратора...
docker compose exec -T backend python scripts/manage.py reset-admin
if errorlevel 1 (
    echo [ERROR] Не удалось создать администратора.
    exit /b 1
)
echo.

REM --- 7. Итог ---
echo ==================================================
echo   ConturAI успешно запущен
echo ==================================================
echo   Frontend:  http://localhost:3000
echo   API:       http://localhost:8000/docs
echo   Status:    http://localhost:8000/status
echo.
echo   Логин и пароль администратора - см. выше в выводе
echo   команды reset-admin. Пароль показывается один раз.
echo ==================================================
echo.

endlocal