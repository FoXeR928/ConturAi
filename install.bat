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
if errorlevel 1 goto try_find_docker
goto check_daemon

:try_find_docker
if exist "%ProgramFiles%\Docker\Docker\resources\bin\docker.exe" (
    set "PATH=%ProgramFiles%\Docker\Docker\resources\bin;%PATH%"
    goto check_daemon
)
echo [ERROR] Docker не найден в системе.
echo.
echo Пожалуйста, установите Docker Desktop:
echo https://www.docker.com/products/docker-desktop/
pause
exit /b 1

:check_daemon
echo [INFO] Проверка подключения к Docker...
docker info >nul 2>&1
if not errorlevel 1 goto daemon_ok

echo [WARN] Docker не запущен. Пытаюсь запустить Docker Desktop...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
) else (
    echo [ERROR] Не удалось найти Docker Desktop.exe.
    echo Запустите Docker Desktop вручную и повторите.
    pause
    exit /b 1
)

set /a RETRIES=0
goto wait_docker

:wait_docker
timeout /t 3 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto daemon_ok

set /a RETRIES+=1
if %RETRIES% GEQ 20 (
    echo [ERROR] Docker не запустился за 60 секунд.
    echo Откройте Docker Desktop вручную и запустите установщик снова.
    pause
    exit /b 1
)
echo    ... ожидание %RETRIES%/20
goto wait_docker

:daemon_ok
echo [INFO] Docker запущен и отвечает.
echo.

echo [INFO] Сборка образа установщика...
docker build -t conturai-installer -f Dockerfile.installer .
if errorlevel 1 goto err_build

echo.
echo [INFO] Запуск установщика ConturAI...
echo.

docker run --rm -it ^
    -v "%cd%:/app" ^
    -v "//./pipe/docker_engine://./pipe/docker_engine" ^
    -w /app ^
    -e HOST_PROJECT_DIR="%cd%" ^
    python:3.12-slim sh -c "apt-get update && apt-get install -y docker.io docker-compose && python install.py"

if errorlevel 1 goto err_install
goto done

:err_build
echo [ERROR] Не удалось собрать образ установщика.
pause
exit /b 1

:err_install
echo [ERROR] Установщик завершился с ошибкой.
pause
exit /b 1

:done
echo.
echo ==================================================
echo   Установка завершена!
echo ==================================================
pause