from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.db.models import User
from app.db.session import get_session
from app.schemas import LlmConfigUpdate
from app.services import llm_config_service

router = APIRouter()


@router.get("/get")
async def get_llm_configs(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    return {
        "result": True,
        "configs": await llm_config_service.list_configs(session),
        "message": "Параметры LLM получены",
        "category": "success",
    }


@router.patch("/update")
async def update_llm_config(
    payload: LlmConfigUpdate,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    await llm_config_service.update_config(session, payload.key, payload.value)
    return {
        "result": True,
        "message": "Параметр LLM обновлён",
        "category": "success",
    }