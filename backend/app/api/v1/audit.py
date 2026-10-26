from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_admin_user
from app.db.models import User, AuditLog
from app.db.session import get_session

router = APIRouter()

@router.get("/list")
async def list_audit_logs(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
):
    # Получаем логи
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    logs = result.scalars().all()
    
    # Общее количество для пагинации
    total = (await session.execute(select(func.count(AuditLog.id)))).scalar_one()

    return {
        "result": True,
        "logs": [
            {
                "id": str(log.id),
                "user_login": log.user_login,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat()
            } for log in logs
        ],
        "total": total
    }