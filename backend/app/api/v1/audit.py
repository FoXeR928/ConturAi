from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_admin_user
from app.db.models import User, AuditLog
from app.db.session import get_session

router = APIRouter()

# ==============================================================================
# БЛОК 1: ПРОСМОТР ЖУРНАЛА АУДИТА (ЛОГОВ ДЕЙСТВИЙ)
# ==============================================================================

@router.get("/list")
async def list_audit_logs(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
):
    """
    Эндпоинт для получения журнала действий пользователей.
    Доступен только администраторам (проверяется через get_admin_user).
    
    Поддерживает пагинацию через query-параметры:
    - limit: сколько записей вернуть (по умолчанию 50)
    - offset: сколько записей пропустить (для переключения страниц)
    """
    
    # 1. Запрос на получение записей логов
    # Сортируем по дате создания (desc), чтобы самые новые события были вверху
    stmt = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    logs = result.scalars().all()
    
    # 2. Подсчет общего количества записей
    # Нужен фронтенду, чтобы отображать количество страниц и рисовать кнопки пагинации
    total = (await session.execute(select(func.count(AuditLog.id)))).scalar_one()

    # 3. Формирование ответа
    # Преобразуем объекты SQLAlchemy в словари для JSON-сериализации.
    # UUID и дату конвертируем в строки, чтобы Pydantic/FastAPI не ругались.
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