from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Plugin
from loguru import logger

async def get_enabled_plugin_ids(session: AsyncSession) -> set[str]:
    """Возвращает множество ID плагинов, которые включены в БД."""
    result = await session.execute(select(Plugin.plugin_id).where(Plugin.is_enabled == True))
    return {row[0] for row in result.all()}

async def list_plugins(session: AsyncSession) -> list[Plugin]:
    """Возвращает список всех записей о плагинах."""
    result = await session.execute(select(Plugin).order_by(Plugin.plugin_id))
    return list(result.scalars().all())

async def toggle_plugin(session: AsyncSession, plugin_id: str, enabled: bool) -> Plugin:
    """Включает или выключает плагин. Создает запись, если её нет."""
    plugin = (await session.execute(select(Plugin).where(Plugin.plugin_id == plugin_id))).scalar_one_or_none()
    
    if not plugin:
        plugin = Plugin(plugin_id=plugin_id, is_enabled=enabled)
        session.add(plugin)
    else:
        plugin.is_enabled = enabled
        
    await session.commit()
    await session.refresh(plugin)
    logger.info(f"Плагин '{plugin_id}' {'включен' if enabled else 'выключен'}")
    return plugin