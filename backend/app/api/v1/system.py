import os
import subprocess
import shutil
import httpx
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.db.models import User
from app.db.session import get_session
from app.services import system_service, llm_config_service
from app.core.config import settings

router = APIRouter()

# Папка для хранения резервных копий. 
# Путь абсолютный, так как скрипт выполняется внутри Docker-контейнера.
# В docker-compose эта папка пробрасывается наружу, чтобы бэкапы не терялись при пересборке.
BACKUP_DIR = Path("/app/data/backups")


# ==============================================================================
# БЛОК 1: МОНИТОРИНГ (МЕТРИКИ СИСТЕМЫ И СТАТУС VLLM)
# ==============================================================================

@router.get("/stats")
async def get_stats(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Эндпоинт для сбора метрик сервера (CPU, RAM, GPU, Диски).
    Вызывается из админки (вкладка «Мониторинг») каждые 5 секунд.
    
    Возвращает два блока:
    1. `stats`: Физические метрики (через system_service, использует psutil/pynvml).
    2. `llm_stats`: Статистика нейросети (кол-во токенов, скорость генерации).
    """
    return {
        "result": True,
        "stats": system_service.get_system_stats(),
        "llm_stats": await system_service.get_llm_stats(session),
        "message": "Метрики получены",
        "category": "success"
    }


@router.get("/vllm-status")
async def get_vllm_status(session: AsyncSession = Depends(get_session)):
    """
    Проверка статуса vLLM (жив ли сервер).
    Используется фронтендом для отображения зеленой/красной лампочки.
    Авторизация не требуется, так как это просто пинг.
    """
    try:
        # Получаем текущий URL vLLM из базы данных
        llm = await llm_config_service.get_typed(session)
        base_url = llm['base_url'].rsplit('/v1', 1)[0]
        
        # Делаем быстрый GET-запрос к эндпоинту /health самого vLLM
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{base_url}/health")
            if resp.status_code == 200:
                return {"status": "ok"}
    except Exception:
        pass # Если vLLM выключен или завис, просто возвращаем offline
    return {"status": "offline"}


# ==============================================================================
# БЛОК 2: РЕЗЕРВНОЕ КОПИРОВАНИЕ (ПРОСМОТР ИНФОРМАЦИИ)
# ==============================================================================

@router.get("/db/backups")
async def list_backups(_: User = Depends(get_admin_user)):
    """
    Получение списка всех существующих бэкапов и размера текущей БД.
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Собираем список файлов в папке с бэкапами
    files = []
    for f in BACKUP_DIR.glob("*"):
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    files.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Получаем размер текущей базы данных (выполняем SQL-запрос прямо в Postgres)
    db_size = subprocess.run(
        ["psql", "-h", settings.db_host, "-U", settings.db_user, "-d", settings.db_name, "-tAc", "SELECT pg_database_size(current_database())"],
        capture_output=True, text=True, env={**os.environ, "PGPASSWORD": settings.db_password}
    ).stdout.strip()

    return {
        "result": True, 
        "backups": files, 
        "db_size": int(db_size) if db_size.isdigit() else 0
    }


# ==============================================================================
# БЛОК 3: РЕЗЕРВНОЕ КОПИРОВАНИЕ (СОЗДАНИЕ АРХИВА)
# ==============================================================================

@router.post("/db/backup")
async def create_backup(_: User = Depends(get_admin_user)):
    """
    Создание нового бэкапа.
    Состоит из двух частей: дамп базы данных и архив загруженных файлов.
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Дамп БД
    # Используем утилиту pg_dump. Пароль передаем через переменную окружения PGPASSWORD.
    db_file = BACKUP_DIR / f"db_{timestamp}.sql"
    res = subprocess.run(
        ["pg_dump", "-h", settings.db_host, "-U", settings.db_user, "-d", settings.db_name, "-f", str(db_file)],
        env={**os.environ, "PGPASSWORD": settings.db_password}, capture_output=True
    )
    if res.returncode != 0:
        raise HTTPException(500, f"Ошибка pg_dump: {res.stderr.decode()}")

    # 2. Архив файлов
    # Запаковываем папку uploads в ZIP-архив через встроенный модуль shutil
    zip_file = BACKUP_DIR / f"uploads_{timestamp}"
    shutil.make_archive(str(zip_file), 'zip', "/app/data/uploads")
    
    return {"result": True, "message": "Бэкап создан"}


# ==============================================================================
# БЛОК 4: РЕЗЕРВНОЕ КОПИРОВАНИЕ (СКАЧИВАНИЕ И УДАЛЕНИЕ)
# ==============================================================================

@router.get("/db/backups/{filename}")
async def download_backup(filename: str, _: User = Depends(get_admin_user)):
    """
    Скачивание конкретного файла бэкапа.
    """
    # ЗАЩИТА ОТ PATH TRAVERSAL: 
    # Проверяем, что в имени файла нет попытки выйти из папки (например, ../../etc/passwd)
    if ".." in filename or "/" in filename:
        raise HTTPException(400, "Invalid filename")
        
    path = BACKUP_DIR / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
        
    return FileResponse(path=str(path), filename=filename)


@router.delete("/db/backups/{filename}")
async def delete_backup(filename: str, _: User = Depends(get_admin_user)):
    """
    Удаление файла бэкапа с диска.
    """
    # Аналогичная проверка на безопасность пути
    if ".." in filename or "/" in filename:
        raise HTTPException(400, "Invalid filename")
        
    path = BACKUP_DIR / filename
    if path.exists():
        path.unlink() # Физическое удаление файла
        
    return {"result": True}