from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Plugin

async def get_enabled_plugin_ids(session: AsyncSession) -> set[str]:
    result = await session.execute(
        select(Plugin.plugin_id).where(Plugin.is_enabled == True)
    )
    return set(result.scalars().all())