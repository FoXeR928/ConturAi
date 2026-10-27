import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DownloadRequest, Upload, User
from app.core.exceptions import AppError

# ==============================================================================
# БЛОК 1: СОЗДАНИЕ ЗАЯВКИ (СТОРОНА ПОЛЬЗОВАТЕЛЯ)
# ==============================================================================

async def create_request(session: AsyncSession, user: User, upload_id: uuid.UUID):
    """
    Создает новую заявку на скачивание файла.
    
    Защита от спама:
    Сначала проверяет, нет ли уже активной заявки (pending) или одобренной (approved).
    Если одобренная заявка уже истекла (expires_at < текущего времени), 
    пользователь может подать новую заявку.
    """
    existing = (await session.execute(
        select(DownloadRequest).where(
            DownloadRequest.user_login == user.login,
            DownloadRequest.upload_id == upload_id,
            DownloadRequest.status.in_(["pending", "approved"]),
            # Условие: заявка либо бессрочная, либо срок еще не истек
            (DownloadRequest.expires_at == None) | (DownloadRequest.expires_at > datetime.now(timezone.utc))
        )
    )).scalar_one_or_none()
    
    if existing:
        raise AppError("Заявка уже создана или активна", "warning", 400)

    # Если нет активной заявки — создаем новую (статус по умолчанию 'pending')
    req = DownloadRequest(user_login=user.login, upload_id=upload_id)
    session.add(req)
    await session.commit()
    return req


# ==============================================================================
# БЛОК 2: ПРОСМОТР ЗАЯВОК (СТОРОНА АДМИНИСТРАТОРА)
# ==============================================================================

async def list_requests(session: AsyncSession):
    """
    Получает список всех заявок на скачивание для панели администратора.
    
    Делает JOIN с таблицей Upload, чтобы вместо технического UUID 
    сразу отдавать фронтенду читаемое имя файла (original_name).
    """
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


# ==============================================================================
# БЛОК 3: ОБРАБОТКА ЗАЯВОК (ОДОБРЕНИЕ/ОТКЛОНЕНИЕ)
# ==============================================================================

async def process_action(session: AsyncSession, req_id: uuid.UUID, action: str):
    """
    Изменяет статус заявки (вызывается админом).
    
    - Если action == "approve": статус меняется на "approved", и устанавливается 
      срок действия доступа (expires_at) на 24 часа вперед.
    - Если action == "reject": статус меняется на "rejected".
    """
    req = (await session.execute(select(DownloadRequest).where(DownloadRequest.id == req_id))).scalar_one_or_none()
    if not req:
        raise AppError("Заявка не найдена", "warning", 404)

    if action == "approve":
        req.status = "approved"
        # Даем доступ на 24 часа с текущего момента
        req.expires_at = datetime.now(timezone.utc) + timedelta(days=1) 
    elif action == "reject":
        req.status = "rejected"
    
    await session.commit()
    return req


# ==============================================================================
# БЛОК 4: ПРОВЕРКА ДОСТУПА К СКАЧИВАНИЮ
# ==============================================================================

async def check_access(session: AsyncSession, user: User, upload_id: uuid.UUID):
    """
    Проверяет, имеет ли пользователь право скачать конкретный файл.
    
    Логика:
    1. Администраторы имеют неограниченный доступ к любым файлам.
    2. Обычные пользователи могут скачивать файл только при наличии 
       одобренной заявки (status="approved"), у которой еще не истек срок (expires_at).
    """
    # 1. Админам доступ всегда разрешен
    if user.is_admin:
        return True
    
    # 2. Для остальных ищем действующее разрешение
    req = (await session.execute(
        select(DownloadRequest).where(
            DownloadRequest.user_login == user.login,
            DownloadRequest.upload_id == upload_id,
            DownloadRequest.status == "approved",
            DownloadRequest.expires_at > datetime.now(timezone.utc)
        )
    )).scalar_one_or_none()
    
    return req is not None