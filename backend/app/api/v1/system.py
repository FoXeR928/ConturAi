import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.api.deps import get_admin_user
from app.db.models import User
from app.services import system_service
from app.core.config import settings

router = APIRouter()
BACKUP_DIR = Path("/app/data/backups")

@router.get("/stats")
async def get_stats(_: User = Depends(get_admin_user)):
    return {"result": True, "stats": system_service.get_system_stats()}

@router.get("/vllm-status")
async def get_vllm_status(session: AsyncSession = Depends(get_session)):
    try:
        llm = await llm_config_service.get_typed(session)
        base_url = llm['base_url'].rsplit('/v1', 1)[0]
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{base_url}/health")
            if resp.status_code == 200:
                return {"status": "ok"}
    except Exception:
        pass
    return {"status": "offline"}

@router.get("/db/backups")
async def list_backups(_: User = Depends(get_admin_user)):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for f in BACKUP_DIR.glob("*"):
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    files.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Размер БД
    db_size = subprocess.run(
        ["psql", "-h", settings.db_host, "-U", settings.db_user, "-d", settings.db_name, "-tAc", "SELECT pg_database_size(current_database())"],
        capture_output=True, text=True, env={**os.environ, "PGPASSWORD": settings.db_password}
    ).stdout.strip()

    return {"result": True, "backups": files, "db_size": int(db_size) if db_size.isdigit() else 0}

@router.post("/db/backup")
async def create_backup(_: User = Depends(get_admin_user)):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Дамп БД
    db_file = BACKUP_DIR / f"db_{timestamp}.sql"
    res = subprocess.run(
        ["pg_dump", "-h", settings.db_host, "-U", settings.db_user, "-d", settings.db_name, "-f", str(db_file)],
        env={**os.environ, "PGPASSWORD": settings.db_password}, capture_output=True
    )
    if res.returncode != 0:
        raise HTTPException(500, f"Ошибка pg_dump: {res.stderr.decode()}")

    # 2. Архив файлов
    zip_file = BACKUP_DIR / f"uploads_{timestamp}"
    shutil.make_archive(str(zip_file), 'zip', "/app/data/uploads")
    
    return {"result": True, "message": "Бэкап создан"}

@router.get("/db/backups/{filename}")
async def download_backup(filename: str, _: User = Depends(get_admin_user)):
    # Защита от Path Traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(400, "Invalid filename")
    path = BACKUP_DIR / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(path=str(path), filename=filename)

@router.delete("/db/backups/{filename}")
async def delete_backup(filename: str, _: User = Depends(get_admin_user)):
    if ".." in filename or "/" in filename:
        raise HTTPException(400, "Invalid filename")
    path = BACKUP_DIR / filename
    if path.exists():
        path.unlink()
    return {"result": True}
