import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DownloadRequest, Upload, Chat, User
from app.core.exceptions import AppError

# ==============================================================================
# БЛОК 1: СОЗДАНИЕ ЗАЯВКИ
# ==============================================================================

async def create_request(
    session: AsyncSession, 
    user: User, 
    upload_id: uuid.UUID | None = None, 
    chat_id: uuid.UUID | None = None
):
    if not upload_id and not chat_id:
        raise AppError("Не указан объект для скачивания", "warning", 400)

    # Формируем условия поиска активной заявки
    conditions = [DownloadRequest.user_login == user.login]
    if upload_id:
        conditions.append(DownloadRequest.upload_id == upload_id)
    if chat_id:
        conditions.append(DownloadRequest.chat_id == chat_id)
        
    existing = (await session.execute(
        select(DownloadRequest).where(
            *conditions,
            DownloadRequest.status.in_(["pending", "approved"]),
            (DownloadRequest.expires_at == None) | (DownloadRequest.expires_at > datetime.now(timezone.utc))
        )
    )).scalar_one_or_none()
    
    if existing:
        raise AppError("Заявка уже создана или активна", "warning", 400)

    req = DownloadRequest(user_login=user.login, upload_id=upload_id, chat_id=chat_id)
    session.add(req)
    await session.commit()
    return req


# ==============================================================================
# БЛОК 2: ПРОСМОТР ЗАЯВОК (АДМИН)
# ==============================================================================

async def list_requests(session: AsyncSession):
    # outerjoin, так как заявка может быть либо на файл, либо на чат
    result = await session.execute(
        select(
            DownloadRequest.id, 
            DownloadRequest.user_login, 
            DownloadRequest.status, 
            DownloadRequest.created_at,
            DownloadRequest.expires_at,
            Upload.original_name.label("file_name"),
            Chat.name.label("chat_name")
        )
        .outerjoin(Upload, Upload.id == DownloadRequest.upload_id)
        .outerjoin(Chat, Chat.id == DownloadRequest.chat_id)
        .order_by(DownloadRequest.created_at.desc())
    )
    return [dict(r._mapping) for r in result.all()]


# ==============================================================================
# БЛОК 3: ОБРАБОТКА ЗАЯВОК
# ==============================================================================

async def process_action(session: AsyncSession, req_id: uuid.UUID, action: str):
    req = (await session.execute(select(DownloadRequest).where(DownloadRequest.id == req_id))).scalar_one_or_none()
    if not req:
        raise AppError("Заявка не найдена", "warning", 404)

    if action == "approve":
        req.status = "approved"
        req.expires_at = datetime.now(timezone.utc) + timedelta(days=1) 
    elif action == "reject":
        req.status = "rejected"
    
    await session.commit()
    return req


# ==============================================================================
# БЛОК 4: ПРОВЕРКА ДОСТУПА
# ==============================================================================

async def check_access(
    session: AsyncSession, 
    user: User, 
    upload_id: uuid.UUID | None = None, 
    chat_id: uuid.UUID | None = None
):
    if user.is_admin:
        return True
    
    conditions = [DownloadRequest.user_login == user.login]
    if upload_id:
        conditions.append(DownloadRequest.upload_id == upload_id)
    if chat_id:
        conditions.append(DownloadRequest.chat_id == chat_id)

    req = (await session.execute(
        select(DownloadRequest).where(
            *conditions,
            DownloadRequest.status == "approved",
            DownloadRequest.expires_at > datetime.now(timezone.utc)
        )
    )).scalar_one_or_none()
    
    return req is not None