from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_admin_user, get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas import DownloadRequestCreate, DownloadRequestAction
from app.services import download_service

router = APIRouter()

# ==============================================================================
# БЛОК 1: ЗАПРОСЫ ПОЛЬЗОВАТЕЛЕЙ (СОЗДАНИЕ ЗАЯВКИ)
# ==============================================================================

@router.post("/request")
async def request_download(
    payload: DownloadRequestCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для создания заявки на скачивание файла.
    
    Доступен любому авторизованному пользователю. 
    В payload передается `upload_id` (ID документа, который пользователь хочет скачать).
    Если у пользователя еще нет одобренной заявки на этот файл, 
    сервис создаст новую со статусом 'pending' (в ожидании).
    """
    await download_service.create_request(session, user, payload.upload_id)
    return {
        "result": True, 
        "message": "Заявка на скачивание отправлена администратору"
    }


# ==============================================================================
# БЛОК 2: АДМИНИСТРИРОВАНИЕ (ПРОСМОТР ЗАЯВОК)
# ==============================================================================

@router.get("/list")
async def list_download_requests(
    _: User = Depends(get_admin_user), # Доступ только для админов
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для получения списка всех заявок на скачивание.
    
    Используется в панели администратора. 
    Сервис возвращает список со всей необходимой информацией: 
    кто запросил (логин), какой файл (имя), текущий статус и дату создания.
    """
    return {
        "result": True, 
        "requests": await download_service.list_requests(session)
    }


# ==============================================================================
# БЛОК 3: АДМИНИСТРИРОВАНИЕ (ОДОБРЕНИЕ ИЛИ ОТКЛОНЕНИЕ)
# ==============================================================================

@router.post("/action")
async def process_download_request(
    payload: DownloadRequestAction,
    _: User = Depends(get_admin_user), # Доступ только для админов
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для обработки заявки (одобрение или отклонение).
    
    В payload передаются:
    - `request_id`: ID конкретной заявки.
    - `action`: строка 'approve' или 'reject'.
    
    Внутри сервиса статус заявки в БД меняется на 'approved' или 'rejected'.
    Если заявка одобрена, пользователь сможет скачать файл.
    """
    await download_service.process_action(session, payload.request_id, payload.action)
    return {
        "result": True, 
        "message": "Статус заявки обновлен"
    }