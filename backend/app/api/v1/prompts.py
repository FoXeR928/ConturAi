from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.db.models import User
from app.db.session import get_session
from app.schemas import PromptUpdate
from app.services import prompt_service

router = APIRouter()

# ==============================================================================
# БЛОК 1: ПОЛУЧЕНИЕ ВСЕХ ПРОМТОВ
# ==============================================================================

@router.get("/get")
async def get_prompts(
    _: User = Depends(get_admin_user), # Доступно только администраторам
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для получения списка всех промтов из базы данных.
    
    Используется на фронтенде во вкладке «Промты». 
    Возвращает массив объектов с ключами (`ai_name`, `system_prompt`, `user_prompt`), 
    их текущими значениями и описанием. Это позволяет администратору 
    видеть текущие инструкции для нейросети и редактировать их.
    """
    return {
        "result": True,
        "prompts": await prompt_service.list_prompts(session),
        "message": "Промты получены",
        "category": "success",
    }


# ==============================================================================
# БЛОК 2: ОБНОВЛЕНИЕ КОНКРЕТНОГО ПРОМТА
# ==============================================================================

@router.patch("/update")
async def update_prompt(
    payload: PromptUpdate,
    _: User = Depends(get_admin_user), # Доступно только администраторам
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для обновления текста промта в базе данных.
    
    Принимает JSON с полями:
    - `key` (например, 'system_prompt' или 'ai_name')
    - `value` (новый текст промта)
    
    Благодаря динамической архитектуре, изменения сохраняются в БД 
    и применяются к следующему же запросу в чат, не требуя перезапуска контейнеров.
    """
    await prompt_service.update_prompt(session, payload.key, payload.value)
    return {
        "result": True, 
        "message": "Промт обновлён", 
        "category": "success"
    }