from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import AuditLog
from loguru import logger

async def log_action(
    session: AsyncSession, 
    user_login: str, 
    action: str, 
    details: str = "", 
    ip_address: str = ""
) -> None:
    try:
        log = AuditLog(
            user_login=user_login,
            action=action,
            details=details,
            ip_address=ip_address
        )
        session.add(log)
        await session.commit()
        logger.info(f"AUDIT: {user_login} -> {action} | {details}")
    except Exception as e:
        logger.error(f"Ошибка записи аудита: {e}")