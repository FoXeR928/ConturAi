@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PYTHON=python"
set "ENV_CMD=python scripts\env_tool.py"
set "MANAGE_DOCKER=docker compose exec -T backend python scripts/manage.py"
set "MANAGE_RUN=docker compose run --rm --no-deps backend python scripts/manage.py"

REM ============ Python ============
python --version >nul 2>&1
if not errorlevel 1 goto :python_ok
echo [INFO] Python не найден — устанавливаю через winget...
where winget >nul 2>&1
if errorlevel 1 (
    echo [ERROR] winget не найден. Установите Python вручную: https://www.python.org/downloads/
    pause & exit /b 1
)
winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts"
where python >nul 2>&1
if errorlevel 1 (
    echo [WARN] Python установлен, но не в PATH. Перезапустите консоль.
    pause & exit /b 1
)
:python_ok

REM ============ Docker ============
where docker >nul 2>&1
if errorlevel 1 (
    echo [INFO] Docker не найден — устанавливаю Docker Desktop...
    where winget >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] winget не найден. Установите Docker Desktop вручную.
        pause & exit /b 1
    )
    winget install --id Docker.DockerDesktop --silent --accept-package-agreements --accept-source-agreements
    echo.
    echo [WARN] Docker Desktop установлен. Нужна перезагрузка Windows.
    pause & exit /b 0
)

docker info >nul 2>&1
if not errorlevel 1 goto :docker_ok
echo [INFO] Docker не запущен — запускаю Docker Desktop...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
) else if exist "%LOCALAPPDATA%\Docker\Docker Desktop.exe" (
    start "" "%LOCALAPPDATA%\Docker\Docker Desktop.exe"
) else (
    echo [ERROR] Не нашёл Docker Desktop.exe.
    pause & exit /b 1
)
set /a tries=0
:wait_docker
docker info >nul 2>&1
if not errorlevel 1 goto :docker_ok
set /a tries+=1
if %tries% GEQ 30 (
    echo [ERROR] Docker не запустился за 60 сек.
    pause & exit /b 1
)
timeout /t 2 /nobreak >nul
goto :wait_docker

:docker_ok
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose недоступен. Обновите Docker Desktop.
    pause & exit /b 1
)

REM ============ git (опционально) ============
where git >nul 2>&1
if errorlevel 1 (
    where winget >nul 2>&1
    if not errorlevel 1 winget install --id Git.Git --silent --accept-package-agreements --accept-source-agreements
)

REM ============ Меню ============
:main_menu
echo.
echo ==================================================
echo   ConturAI
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

:pick_platform
echo.
echo Выберите платформу:
echo   1^) nvidia   2^) amd   3^) cpu   4^) dev
set /p P=[1]: 
if "%P%"=="" set P=1
if "%P%"=="1" set MODE=nvidia
if "%P%"=="2" set MODE=amd
if "%P%"=="3" set MODE=cpu
if "%P%"=="4" set MODE=dev
if not defined MODE ( echo [ERROR] Неверный выбор. & exit /b 1 )
%ENV_CMD% setup-env
%ENV_CMD% use-platform !MODE!
exit /b 0

:full_install
call :pick_platform
if errorlevel 1 exit /b 1
echo [INFO] Сборка backend...
docker compose build backend
if errorlevel 1 ( pause & exit /b 1 )
echo [INFO] Скачивание моделей...
%MANAGE_RUN% download-models
if errorlevel 1 ( pause & exit /b 1 )
echo [INFO] Запуск контейнеров...
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
echo   1^) up -d   2^) stop   3^) restart   4^) up -d --build
echo   5^) down    6^) down -v   7^) logs -f   8^) ps   0^) Назад
set /p C=Номер: 
if "%C%"=="0" exit /b 0
if "%C%"=="1" docker compose up -d
if "%C%"=="2" docker compose stop
if "%C%"=="3" docker compose restart
if "%C%"=="4" docker compose up -d --build
if "%C%"=="5" docker compose down
if "%C%"=="6" (
    set /p ok=Удалить тома с БД? (y/N): 
    if /i "!ok!"=="y" docker compose down -v
)
if "%C%"=="7" docker compose logs -f
if "%C%"=="8" docker compose ps
goto containers_menu

:manage_menu
echo.
echo --- manage.py ---
echo   1^) setup-env       2^) use-platform nvidia
echo   3^) use-platform amd   4^) use-platform cpu
echo   5^) use-platform dev   6^) download-models
echo   7^) download-models --only   8^) init-db
echo   9^) reset-admin    10^) set-llm   0^) Назад
set /p M=Номер: 
if "%M%"=="0" exit /b 0
if "%M%"=="1" %ENV_CMD% setup-env
if "%M%"=="2" %ENV_CMD% use-platform nvidia
if "%M%"=="3" %ENV_CMD% use-platform amd
if "%M%"=="4" %ENV_CMD% use-platform cpu
if "%M%"=="5" %ENV_CMD% use-platform dev
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
    if not "!temp!"==""  set "args=!args! --temperature !temp!"
    if not "!mt!"==""    set "args=!args! --max-tokens !mt!"
    %MANAGE_DOCKER% set-llm !args!
)
goto manage_menu