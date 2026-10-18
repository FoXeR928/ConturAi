from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.services import user_service

router = APIRouter()


@router.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    expires_use: bool = Form(False),
    session: AsyncSession = Depends(get_session),
):
    token = await user_service.authenticate(
        session, form.username, form.password, long_lived=expires_use
    )
    return {
        "result": True,
        "access_token": token,
        "token_type": "bearer",
        "message": "Авторизация прошла успешно",
        "category": "success",
    }


@router.post("/logout")
async def logout(_: User = Depends(get_current_user)):
    return {
        "result": True,
        "message": "Пользователь деавторизирован",
        "category": "success",
    }