from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.db.models import Plugin, User
from app.db.session import get_session

router = APIRouter()

@router.get("/active")
async def get_active_plugins(session: AsyncSession = Depends(get_session)):
    """Возвращает список включенных плагинов для фронтенда."""
    result = await session.execute(
        select(Plugin.plugin_id).where(Plugin.is_enabled == True)
    )
    return {"result": True, "plugins": list(result.scalars().all())}

@router.get("/list")
async def list_all_plugins(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Список всех плагинов (включая выключенные) для админки."""
    result = await session.execute(select(Plugin))
    return {"result": True, "plugins": [
        {"id": p.plugin_id, "enabled": p.is_enabled} for p in result.scalars().all()
    ]}

# ДОБАВИТЬ ЭТОТ ЭНДПОИНТ:
@router.patch("/toggle")
async def toggle_plugin(
    payload: PluginToggle,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session)
):
    plugin = (await session.execute(select(Plugin).where(Plugin.plugin_id == payload.id))).scalar_one_or_none()
    if not plugin:
        # Если плагина нет в БД, создаем его включенным
        session.add(Plugin(plugin_id=payload.id, is_enabled=True))
    else:
        plugin.is_enabled = not plugin.is_enabled
    
    await session.commit()
    return {"result": True, "message": "Статус плагина изменен"}