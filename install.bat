@echo off
chcp 65001 >nul

echo ==================================================
echo   ConturAI - Запуск установки через WSL
echo ==================================================

:: Проверяем, установлен ли WSL
wsl --status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] WSL не установлен или не настроен.
    echo Пожалуйста, откройте PowerShell от имени администратора и выполните:
    echo wsl --install
    pause
    exit /b 1
)

:: Запускаем install.sh внутри WSL
:: Команда wsl автоматически переходит в текущую папку
echo [INFO] Передача управления в Linux (WSL)...
wsl bash -c "chmod +x install.sh && ./install.sh"

pause