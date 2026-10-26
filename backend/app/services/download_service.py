import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import DownloadRequest, Upload, User
from app.core.exceptions import AppError

async def create_request(session: AsyncSession, user: User, upload_id: uuid.UUID):
    # Проверяем, нет ли уже активной заявки
    existing = (await session.execute(
        select(DownloadRequest).where(
            DownloadRequest.user_login == user.login,
            DownloadRequest.upload_id == upload_id,
            DownloadRequest.status.in_(["pending", "approved"]),
            (DownloadRequest.expires_at == None) | (DownloadRequest.expires_at > datetime.now(timezone.utc))
        )
    )).scalar_one_or_none()
    
    if existing:
        raise AppError("Заявка уже создана или активна", "warning", 400)

    req = DownloadRequest(user_login=user.login, upload_id=upload_id)
    session.add(req)
    await session.commit()
    return req

async def list_requests(session: AsyncSession):
    result = await session.execute(
        select(
            DownloadRequest.id, 
            DownloadRequest.user_login, 
            DownloadRequest.status, 
            DownloadRequest.created_at,
            DownloadRequest.expires_at,
            Upload.original_name
        )
        .join(Upload, Upload.id == DownloadRequest.upload_id)
        .order_by(DownloadRequest.created_at.desc())
    )
    return [dict(r._mapping) for r in result.all()]

async def process_action(session: AsyncSession, req_id: uuid.UUID, action: str):
    req = (await session.execute(select(DownloadRequest).where(DownloadRequest.id == req_id))).scalar_one_or_none()
    if not req:
        raise AppError("Заявка не найдена", "warning", 404)

    if action == "approve":
        req.status = "approved"
        req.expires_at = datetime.now(timezone.utc) + timedelta(days=1) # Доступ на 24 часа
    elif action == "reject":
        req.status = "rejected"
    
    await session.commit()
    return req

async def check_access(session: AsyncSession, user: User, upload_id: uuid.UUID):
    # Админам доступ всегда разрешен
    if user.is_admin:
        return True
    
    # Проверяем заявку
    req = (await session.execute(
        select(DownloadRequest).where(
            DownloadRequest.user_login == user.login,
            DownloadRequest.upload_id == upload_id,
            DownloadRequest.status == "approved",
            DownloadRequest.expires_at > datetime.now(timezone.utc)
        )
    )).scalar_one_or_none()
    
    return req is not None