from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import create_access_token
from app.db.models import User


async def authenticate(
    session: AsyncSession, login: str, password: str, long_lived: bool = False
) -> str:
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()

    if not user or not user.check_password(password):
        raise AppError("Неверный логин или пароль", "warning", 401)
    return create_access_token(login, long_lived=long_lived)