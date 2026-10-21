@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] python не найден.
    exit /b 1
)
docker --version >nul 2>&1
if errorlevel 1 ( echo [ERROR] Docker не найден. & exit /b 1 )
docker compose version >nul 2>&1
if errorlevel 1 ( echo [ERROR] Docker Compose не найден. & exit /b 1 )

set "MANAGE_HOST=python backend\scripts\manage.py"
set "MANAGE_DOCKER=docker compose exec -T backend python scripts/manage.py"
set "MANAGE_RUN=docker compose run --rm --no-deps backend python scripts/manage.py"

goto main_menu

:ensure_env
if not exist .env (
    echo [INFO] Генерация .env...
    %MANAGE_HOST% setup-env
)
exit /b 0

:pick_platform
echo.
echo Выберите платформу:
echo   1^) nvidia
echo   2^) amd
echo   3^) cpu
echo   4^) dev
set /p P=[1]: 
if "%P%"=="" set P=1
if "%P%"=="1" set MODE=nvidia
if "%P%"=="2" set MODE=amd
if "%P%"=="3" set MODE=cpu
if "%P%"=="4" set MODE=dev
if not defined MODE ( echo [ERROR] Неверный выбор. & exit /b 1 )
call :ensure_env
%MANAGE_HOST% use-platform !MODE!
exit /b 0

:full_install
call :pick_platform
if errorlevel 1 exit /b 1
echo [INFO] Скачивание моделей...
%MANAGE_RUN% download-models
if errorlevel 1 exit /b 1
echo [INFO] Сборка и запуск...
docker compose up -d --build
echo [INFO] Ожидание...
timeout /t 10 /nobreak >nul
%MANAGE_DOCKER% init-db
%MANAGE_DOCKER% reset-admin
echo [OK] Установка завершена.
exit /b 0

:containers_menu
echo.
echo --- Контейнеры ---
echo   1^) up -d
echo   2^) stop
echo   3^) restart
echo   4^) up -d --build
echo   5^) down
echo   6^) down -v (удалит БД)
echo   7^) logs -f
echo   8^) ps
echo   0^) Назад
set /p C=Номер: 
if "%C%"=="0" exit /b 0
if "%C%"=="1" docker compose up -d
if "%C%"=="2" docker compose stop
if "%C%"=="3" docker compose restart
if "%C%"=="4" docker compose up -d --build
if "%C%"=="5" docker compose down
if "%C%"=="6" (
    set /p ok=Точно удалить тома? (y/N): 
    if /i "!ok!"=="y" docker compose down -v
)
if "%C%"=="7" docker compose logs -f
if "%C%"=="8" docker compose ps
goto containers_menu

:manage_menu
call :ensure_env
echo.
echo --- manage.py ---
echo   1^) setup-env
echo   2^) use-platform nvidia
echo   3^) use-platform amd
echo   4^) use-platform cpu
echo   5^) use-platform dev
echo   6^) download-models
echo   7^) download-models --only
echo   8^) init-db
echo   9^) reset-admin
echo  10^) set-llm
echo   0^) Назад
set /p M=Номер: 
if "%M%"=="0" exit /b 0
if "%M%"=="1" %MANAGE_HOST% setup-env
if "%M%"=="2" %MANAGE_HOST% use-platform nvidia
if "%M%"=="3" %MANAGE_HOST% use-platform amd
if "%M%"=="4" %MANAGE_HOST% use-platform cpu
if "%M%"=="5" %MANAGE_HOST% use-platform dev
if "%M%"=="6" %MANAGE_RUN% download-models
if "%M%"=="7" (
    set /p only=repo:name,repo:name: 
    %MANAGE_RUN% download-models --only "!only!"
)
if "%M%"=="8" %MANAGE_DOCKER% init-db
if "%M%"=="9" %MANAGE_DOCKER% reset-admin
if "%M%"=="10" (
    set /p model=model: 
    set /p temp=temperature: 
    set /p mt=max-tokens: 
    set "args="
    if not "!model!"=="" set "args=!args! --model !model!"
    if not "!temp!"=="" set "args=!args! --temperature !temp!"
    if not "!mt!"=="" set "args=!args! --max-tokens !mt!"
    %MANAGE_DOCKER% set-llm !args!
)
goto manage_menu

:main_menu
echo.
echo ==================================================
echo   ConturAI - установка и управление
echo ==================================================
echo   1^) Полная установка
echo   2^) Управление контейнерами
echo   3^) Команды manage.py
echo   4^) Выход
set /p MAIN=[1]: 
if "%MAIN%"=="" set MAIN=1
if "%MAIN%"=="1" call :full_install & goto main_menu
if "%MAIN%"=="2" call :containers_menu & goto main_menu
if "%MAIN%"=="3" call :manage_menu & goto main_menu
if "%MAIN%"=="4" exit /b 0
goto main_menu