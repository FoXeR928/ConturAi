from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.db.models import User
from app.db.session import get_session
from app.schemas import LlmConfigUpdate
from app.services import llm_config_service

router = APIRouter()

# ==============================================================================
# БЛОК 1: ПОЛУЧЕНИЕ ДИНАМИЧЕСКИХ НАСТРОЕК LLM
# ==============================================================================

@router.get("/get")
async def get_llm_configs(
    _: User = Depends(get_admin_user), # Доступ только для администраторов
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для получения списка всех настроек LLM и RAG из базы данных.
    
    Используется на фронтенде во вкладке «Параметры LLM». 
    Возвращает массив объектов, содержащих ключ (key), текущее значение (value), 
    описание (description) и тип поля (input_type), чтобы фронтенд знал, 
    рисовать ему текстовое поле, число или чекбокс.
    """
    return {
        "result": True,
        "configs": await llm_config_service.list_configs(session),
        "message": "Параметры LLM получены",
        "category": "success",
    }


# ==============================================================================
# БЛОК 2: ОБНОВЛЕНИЕ КОНКРЕТНОГО ПАРАМЕТРА
# ==============================================================================

@router.patch("/update")
async def update_llm_config(
    payload: LlmConfigUpdate,
    _: User = Depends(get_admin_user), # Доступ только для администраторов
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для обновления одного параметра в базе данных.
    
    Принимает JSON с полями `key` (название параметра) и `value` (новое значение).
    Благодаря архитектуре проекта, эти изменения применяются к следующему 
    запросу в чат на лету (перезапуск контейнеров не требуется).
    """
    # Сервис сам найдет запись по ключу и обновит её значение
    await llm_config_service.update_config(session, payload.key, payload.value)
    
    return {
        "result": True,
        "message": "Параметр LLM обновлён",
        "category": "success",
    }