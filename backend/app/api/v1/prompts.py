from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.db.models import User
from app.db.session import get_session
from app.schemas import PromptUpdate
from app.services import prompt_service

router = APIRouter()


@router.get("/get")
async def get_prompts(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    return {
        "result": True,
        "prompts": await prompt_service.list_prompts(session),
        "message": "Промты получены",
        "category": "success",
    }


@router.patch("/update")
async def update_prompt(
    payload: PromptUpdate,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    await prompt_service.update_prompt(session, payload.key, payload.value)
    return {"result": True, "message": "Промт обновлён", "category": "success"}