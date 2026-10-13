from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.models import ApiToken, User
from app.db.session import get_session
from app.services import auth_service

router = APIRouter()


@router.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    expires_use: bool = Form(False),
    session: AsyncSession = Depends(get_session),
):
    token = await auth_service.authenticate(
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


@router.get("/get_token")
async def get_token(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    row = (
        await session.execute(select(ApiToken).where(ApiToken.id == 1))
    ).scalar_one_or_none()
    if not row or not row.token:
        return {
            "result": False,
            "message": "Токен не создан",
            "category": "warning",
        }
    return {
        "result": True,
        "token_api": row.token,
        "date_create": row.created_at,
        "message": "Токен получен",
        "category": "success",
    }


@router.put("/create_token")
async def create_token(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    import secrets

    row = (
        await session.execute(select(ApiToken).where(ApiToken.id == 1))
    ).scalar_one_or_none()
    if not row:
        row = ApiToken(id=1)
        session.add(row)
    row.token = secrets.token_hex(64)
    await session.commit()
    return {
        "result": True,
        "token_api": row.token,
        "message": "Токен создан",
        "category": "success",
    }