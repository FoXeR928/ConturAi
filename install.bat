@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PROJECT_DIR=%cd%"

echo ==================================================
echo   ConturAI - Установщик
echo ==================================================
echo.

REM --- Проверка наличия Docker в PATH ---
where docker >nul 2>&1
if errorlevel 1 (
    REM Пробуем найти Docker в стандартных местах установки
    if exist "%ProgramFiles%\Docker\Docker\resources\bin\docker.exe" (
        set "PATH=%ProgramFiles%\Docker\Docker\resources\bin;%PATH%"
    ) else (
        echo [ERROR] Docker не найден в системе.
        echo.
        echo Пожалуйста, установите Docker Desktop:
        echo https://www.docker.com/products/docker-desktop/
        pause & exit /b 1
    )
)

REM --- Проверка, что демон Docker запущен ---
echo [INFO] Проверка подключения к Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [WARN] Docker не запущен. Пытаюсь запустить Docker Desktop...
    
    if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
        start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    )
    
    echo [INFO] Ожидание запуска Docker (это может занять до 1 минуты)...
    set /a RETRIES=0
    :wait_docker
    timeout /t 3 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 (
        set /a RETRIES+=1
        if !RETRIES! GEQ 20 (
            echo [ERROR] Docker не запустился за 60 секунд.
            echo Пожалуйста, откройте Docker Desktop вручную и запустите установщик снова.
            pause & exit /b 1
        )
        echo    ... ожидание !RETRIES!/20
        goto wait_docker
    )
    echo [INFO] Docker успешно запущен.
) else (
    echo [INFO] Docker уже запущен.
)

echo.
echo [INFO] Сборка образа установщика...
docker build -t conturai-installer -f Dockerfile.installer .
if errorlevel 1 (
    echo [ERROR] Не удалось собрать образ установщика.
    pause & exit /b 1
)

echo.
echo [INFO] Запуск установщика ConturAI...
echo.

REM ВАЖНО: На Windows используем named pipe для Docker
docker run --rm -it ^
    -v "%PROJECT_DIR%:/app" ^
    -v "//./pipe/docker_engine://./pipe/docker_engine" ^
    -w /app ^
    -e HOST_PROJECT_DIR="%PROJECT_DIR%" ^
    conturai-installer python install.py

if errorlevel 1 (
    echo.
    echo [ERROR] Установщик завершился с ошибкой.
    pause & exit /b 1
)

echo.
echo ==================================================
echo   Установка завершена!
echo ==================================================
pause