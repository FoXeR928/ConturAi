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

@router.get("/get")
async def get_examples(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
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

@router.post("/create")
async def create_example(
    payload: FewShotCreate,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    if not payload.question.strip() or not payload.answer.strip():
        raise AppError("Вопрос и ответ не могут быть пустыми", "warning", 400)
        
    example = FewShot(question=payload.question, answer=payload.answer)
    session.add(example)
    await session.commit()
    return {"result": True, "message": "Пример добавлен"}

@router.delete("/{example_id}")
async def delete_example(
    example_id: UUID,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    await session.execute(delete(FewShot).where(FewShot.id == example_id))
    await session.commit()
    return {"result": True, "message": "Пример удален"}