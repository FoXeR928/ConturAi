from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas import TagCreate
from app.services import tag_service

router = APIRouter()

# ==============================================================================
# БЛОК 1: ПОЛУЧЕНИЕ СПИСКА ТЕГОВ
# ==============================================================================

@router.get("/get")
async def get_tags(
    _: User = Depends(get_current_user), # Доступно любому авторизованному пользователю
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для получения списка всех тегов.
    
    Вызывается со стороны фронтенда (в чате и в фильтрах), чтобы 
    отрисовать выпадающий список доступных тегов.
    Возвращает массив объектов: id, name, color.
    """
    tags = await tag_service.list_tags(session)
    return {
        "result": True, 
        "tags": tags
    }


# ==============================================================================
# БЛОК 2: СОЗДАНИЕ НОВОГО ТЕГА
# ==============================================================================

@router.post("/create")
async def create_tag(
    payload: TagCreate,
    _: User = Depends(get_admin_user), # Доступно ТОЛЬКО администратору
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для создания нового тега.
    
    Принимает название тега (`name`) и его цвет в HEX-формате (`color`).
    Сервис проверяет, нет ли уже тега с таким названием, 
    и если нет — сохраняет его в базу.
    """
    await tag_service.create_tag(session, payload.name, payload.color)
    return {
        "result": True, 
        "message": "Тег создан"
    }


# ==============================================================================
# БЛОК 3: УДАЛЕНИЕ ТЕГА
# ==============================================================================

@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: UUID,
    _: User = Depends(get_admin_user), # Доступно ТОЛЬКО администратору
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для удаления тега по его ID.
    
    Удаляет запись из справочника тегов.
    (В будущем здесь можно добавить логику очистки этого тега 
    из всех привязанных к нему документов и чатов).
    """
    await tag_service.delete_tag(session, tag_id)
    return {
        "result": True, 
        "message": "Тег удалён"
    }