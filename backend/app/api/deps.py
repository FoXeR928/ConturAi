from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.secrets import decode_token
from app.db.models import User
from app.db.session import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        login = decode_token(token)
    except Exception as err:
        raise AppError("Неверный токен", "warning", 401) from err
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    if not user or user.disabled:
        raise AppError("Пользователь не найден", "warning", 401)
    return user


async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise AppError("Доступно только администратору", "warning", 403)
    return user