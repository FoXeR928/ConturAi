from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas import DownloadRequestCreate, DownloadRequestAction
from app.services import download_service

router = APIRouter()

@router.post("/request")
async def request_download(
    payload: DownloadRequestCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Создание заявки на скачивание (файла или чата)."""
    await download_service.create_request(
        session, 
        user, 
        upload_id=payload.upload_id, 
        chat_id=payload.chat_id
    )
    return {"result": True, "message": "Заявка на скачивание отправлена администратору"}

@router.get("/list")
async def list_download_requests(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """Список всех заявок (для админ-панели)."""
    return {"result": True, "requests": await download_service.list_requests(session)}

@router.post("/action")
async def process_download_request(
    payload: DownloadRequestAction,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """Одобрение или отклонение заявки."""
    await download_service.process_action(session, payload.request_id, payload.action)
    return {"result": True, "message": "Статус заявки обновлен"}