# Как запускать локально

1. Установить зависимости один раз:
   cd conturai-manager  && pip install -r requirements.txt
   cd ../conturai-backend && pip install -r requirements.txt
   cd ../conturai-frontend && npm install
   cd ..

2. Скопировать примеры конфигов:
   cp conturai-manager/.env.example conturai-manager/.env
   cp conturai-backend/.env.example conturai-backend/.env
   # (dev.py сделает это автоматически, если .env отсутствует)

3. Запустить весь стек одной командой:
   ./scripts/dev.sh          # Linux / macOS
   .\scripts\dev.ps1         # Windows

   Или напрямую:
   python scripts/dev.py

   dev.py сам:
     - поднимет postgres в Docker
     - запустит manager на :8080
     - запустит backend на :8000
     - запустит frontend (Vite) на :5173
     - проксирует /api → :8000
     - остановит всё по Ctrl+C