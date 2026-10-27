from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.db.models import User, FewShot
from app.db.session import get_session
from app.schemas import FewShotCreate
from app.core.exceptions import AppError

router = APIRouter()

# ==============================================================================
# БЛОК 1: ПРОСМОТР ПРИМЕРОВ (FEW-SHOT)
# ==============================================================================

@router.get("/get")
async def get_examples(
    _: User = Depends(get_admin_user), # Доступно только администраторам
    session: AsyncSession = Depends(get_session),
):
    """
    Получение списка всех сохраненных примеров (пар "вопрос-ответ").
    
    Используется в админ-панели для отображения текущих Few-Shot примеров,
    которые помогают нейросети лучше понимать формат ожидаемых ответов.
    Сортировка: сначала самые новые.
    """
    result = await session.execute(select(FewShot).order_by(FewShot.created_at.desc()))
    examples = result.scalars().all()
    return {
        "result": True,
        "examples": [
            {"id": str(e.id), "question": e.question, "answer": e.answer} 
            for e in examples
        ],
        "message": "Примеры получены"
    }


# ==============================================================================
# БЛОК 2: ДОБАВЛЕНИЕ НОВОГО ПРИМЕРА
# ==============================================================================

@router.post("/create")
async def create_example(
    payload: FewShotCreate,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Создание нового Few-Shot примера.
    
    Проверяет, что поля вопроса и ответа не пустые (и не состоят из одних пробелов).
    Если проверка пройдена, сохраняет пример в базу данных.
    """
    # Валидация входных данных: отсекаем пустые строки и строки из пробелов
    if not payload.question.strip() or not payload.answer.strip():
        raise AppError("Вопрос и ответ не могут быть пустыми", "warning", 400)
        
    example = FewShot(question=payload.question, answer=payload.answer)
    session.add(example)
    await session.commit()
    return {"result": True, "message": "Пример добавлен"}


# ==============================================================================
# БЛОК 3: УДАЛЕНИЕ ПРИМЕРА
# ==============================================================================

@router.delete("/{example_id}")
async def delete_example(
    example_id: UUID,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Удаление Few-Shot примера по его ID.
    
    Выполняет прямой DELETE-запрос в базу данных. 
    Если примера с таким ID нет, ошибка не выбрасывается (идемпотентное удаление).
    """
    await session.execute(delete(FewShot).where(FewShot.id == example_id))
    await session.commit()
    return {"result": True, "message": "Пример удален"}