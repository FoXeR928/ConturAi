@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ============ Docker ============
where docker >nul 2>&1
if errorlevel 1 (
    echo ============================================================
    echo Docker не найден.
    echo Установите Docker Desktop вручную:
    echo   https://docs.docker.com/desktop/install/windows-install/
    echo После установки и перезагрузки запустите этот файл снова.
    echo ============================================================
    pause
    exit /b 1
)

docker info >nul 2>&1
if not errorlevel 1 goto :docker_ok
echo [INFO] Docker не запущен — открываю Docker Desktop...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
) else if exist "%LOCALAPPDATA%\Docker\Docker Desktop.exe" (
    start "" "%LOCALAPPDATA%\Docker\Docker Desktop.exe"
) else (
    echo [ERROR] Не нашёл Docker Desktop.exe. Запустите Docker Desktop вручную.
    pause & exit /b 1
)
set /a tries=0
:wait_docker
docker info >nul 2>&1
if not errorlevel 1 goto :docker_ok
set /a tries+=1
if %tries% GEQ 30 (
    echo [ERROR] Docker не запустился за 60 секунд.
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

REM ============ .env и compose (без Python) ============
set "MANAGE_DOCKER=docker compose exec -T backend python scripts/manage.py"
set "MANAGE_RUN=docker compose run --rm --no-deps backend python scripts/manage.py"

goto main_menu

REM ---------- .env ----------
:setup_env
if exist .env (
    echo [INFO] .env уже существует — пропускаю
    exit /b 0
)
if not exist .env.example (
    echo [ERROR] Не найден .env.example
    exit /b 1
)
echo [INFO] Создаю .env...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$pass = -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_});" ^
  "$c = Get-Content -Raw .env.example;" ^
  "$c = $c -replace 'DB_USER=.*', 'DB_USER=conturai_user';" ^
  "$c = $c -replace 'DB_PASSWORD=.*', ('DB_PASSWORD=' + $pass);" ^
  "Set-Content -NoNewline -Encoding UTF8 .env $c;"
if errorlevel 1 exit /b 1
echo [OK] .env создан
exit /b 0

REM ---------- use-platform ----------
:use_platform
set "PLAT=%~1"
set "SRC=templates\docker-compose.%PLAT%.yml"
if not exist "%SRC%" (
    echo [ERROR] Не найден шаблон %SRC%
    exit /b 1
)
copy /Y "%SRC%" docker-compose.yml >nul
echo [OK] docker-compose.yml перезаписан (%PLAT%)

if "%PLAT%"=="nvidia" (
    set "IDX=https://download.pytorch.org/whl/cu121"
    set "DTYPE=auto"
    set "KVC="
    set "MAXLEN=4096"
    set "VLLM_MEM=12g"
    set "PG_MEM=1g"
    set "BE_MEM=2g"
    set "FE_MEM=256m"
    set "EMB_PATH=/models/multilingual-e5-large"
    set "EMB_DIM=1024"
    set "MODELS=intfloat/multilingual-e5-large:multilingual-e5-large,Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
)
if "%PLAT%"=="amd" (
    set "IDX=https://download.pytorch.org/whl/rocm6.1"
    set "DTYPE=auto"
    set "KVC="
    set "MAXLEN=4096"
    set "VLLM_MEM=12g"
    set "PG_MEM=1g"
    set "BE_MEM=2g"
    set "FE_MEM=256m"
    set "EMB_PATH=/models/multilingual-e5-large"
    set "EMB_DIM=1024"
    set "MODELS=intfloat/multilingual-e5-large:multilingual-e5-large,Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
)
if "%PLAT%"=="cpu" (
    set "IDX=https://download.pytorch.org/whl/cpu"
    set "DTYPE=float32"
    set "KVC=4"
    set "MAXLEN=2048"
    set "VLLM_MEM=8g"
    set "PG_MEM=1g"
    set "BE_MEM=2g"
    set "FE_MEM=256m"
    set "EMB_PATH=/models/multilingual-e5-large"
    set "EMB_DIM=1024"
    set "MODELS=intfloat/multilingual-e5-large:multilingual-e5-large,Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
)
if "%PLAT%"=="dev" (
    set "IDX=https://download.pytorch.org/whl/cpu"
    set "DTYPE=float32"
    set "KVC=1"
    set "MAXLEN=1024"
    set "VLLM_MEM=3g"
    set "PG_MEM=1g"
    set "BE_MEM=1g"
    set "FE_MEM=256m"
    set "EMB_PATH=/models/granite-embedding-97m-multilingual-r2"
    set "EMB_DIM=384"
    set "MODELS=ibm-granite/granite-embedding-97m-multilingual-r2:granite-embedding-97m-multilingual-r2,Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$k=@{'PYTORCH_INDEX'='%IDX%';'VLLM_DTYPE'='%DTYPE%';'VLLM_CPU_KVCACHE_SPACE'='%KVC%';'VLLM_MAX_MODEL_LEN'='%MAXLEN%';'VLLM_MEM_LIMIT'='%VLLM_MEM%';'PG_MEM_LIMIT'='%PG_MEM%';'BACKEND_MEM_LIMIT'='%BE_MEM%';'FRONTEND_MEM_LIMIT'='%FE_MEM%';'EMBEDDING_MODEL_PATH'='%EMB_PATH%';'EMBEDDING_DIM'='%EMB_DIM%';'MODELS_TO_DOWNLOAD'='%MODELS%'};" ^
  "$c=Get-Content -Raw .env;" ^
  "foreach($key in $k.Keys){ if($c -match \"$key=\"){ $c = $c -replace \"$key=.*\", \"$key=$($k[$key])\" } else { if(-not $c.EndsWith(\"`n\")){$c += \"`n\"}; $c += \"$key=$($k[$key])\" } };" ^
  "Set-Content -NoNewline -Encoding UTF8 .env $c;"
if errorlevel 1 exit /b 1
exit /b 0

REM ---------- pick platform ----------
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
if not defined MODE ( echo [ERROR] Неверный выбор & exit /b 1 )
call :setup_env
call :use_platform !MODE!
exit /b 0

REM ---------- full install ----------
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

REM ---------- containers ----------
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

REM ---------- manage ----------
:manage_menu
echo.
echo --- manage.py (в контейнере) ---
echo   1^) init-db   2^) reset-admin   3^) download-models
echo   4^) download-models --only   5^) set-llm
echo   6^) use-platform nvidia  7^) amd  8^) cpu  9^) dev
echo   0^) Назад
set /p M=Номер: 
if "%M%"=="0" exit /b 0
if "%M%"=="1" %MANAGE_DOCKER% init-db
if "%M%"=="2" %MANAGE_DOCKER% reset-admin
if "%M%"=="3" %MANAGE_RUN% download-models
if "%M%"=="4" (
    set /p only=repo:name,repo:name: 
    %MANAGE_RUN% download-models --only "!only!"
)
if "%M%"=="5" (
    set /p model=model: 
    set /p temp=temperature: 
    set /p mt=max-tokens: 
    set "args="
    if not "!model!"=="" set "args=!args! --model !model!"
    if not "!temp!"==""  set "args=!args! --temperature !temp!"
    if not "!mt!"==""    set "args=!args! --max-tokens !mt!"
    %MANAGE_DOCKER% set-llm !args!
)
if "%M%"=="6" ( call :setup_env & call :use_platform nvidia )
if "%M%"=="7" ( call :setup_env & call :use_platform amd )
if "%M%"=="8" ( call :setup_env & call :use_platform cpu )
if "%M%"=="9" ( call :setup_env & call :use_platform dev )
goto manage_menu

REM ---------- main menu ----------
:main_menu
echo.
echo ==================================================
echo   ConturAI
echo ==================================================
echo   1^) Полная установка
echo   2^) Управление контейнерами
echo   3^) Команды manage.py (в контейнере)
echo   4^) Выход
set /p MAIN=[1]: 
if "%MAIN%"=="" set MAIN=1
if "%MAIN%"=="1" call :full_install & goto main_menu
if "%MAIN%"=="2" call :containers_menu & goto main_menu
if "%MAIN%"=="3" call :manage_menu & goto main_menu
if "%MAIN%"=="4" exit /b 0
goto main_menu