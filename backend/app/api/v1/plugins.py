from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import get_admin_user
from app.db.models import User
from app.db.session import get_session, async_session_factory
from app.core.plugin_manager import plugin_manager
from app.services import plugin_service

router = APIRouter()

class ToggleRequest(BaseModel):
    enabled: bool

@router.get("/list")
async def list_plugins(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """Список всех найденных плагинов + их состояние из БД"""
    db_plugins = {p.plugin_id: p.is_enabled for p in await plugin_service.list_plugins(session)}
    
    result = []
    for pid, meta in plugin_manager.registry.items():
        result.append({
            "id": pid,
            "name": meta.get("name", pid),
            "version": meta.get("version", "unknown"),
            "description": meta.get("description", ""),
            "icon": meta.get("icon", "Puzzle"),
            "type": meta.get("type", "unknown"),
            "is_enabled": db_plugins.get(pid, True) # По умолчанию включен
        })
    return {"result": True, "plugins": result}

@router.patch("/{plugin_id}/toggle")
async def toggle_plugin(
    plugin_id: str,
    payload: ToggleRequest,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """Включает/выключает плагин и перезагружает его в памяти"""
    await plugin_service.toggle_plugin(session, plugin_id, payload.enabled)
    
    # Перезагружаем менеджер плагинов
    async with async_session_factory() as reload_session:
        await plugin_manager.load_plugins(reload_session)
        
    return {"result": True, "message": "Плагин обновлен"}