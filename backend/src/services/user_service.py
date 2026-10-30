from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import User
from ..security import hash_password, verify_password

logger = logging.getLogger("conturai.backend.users")


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate(db: AsyncSession, username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


async def create_user(
    db: AsyncSession, username: str, password: str, role: str = "user"
) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def ensure_admin(db: AsyncSession) -> None:
    result = await db.execute(select(func.count()).select_from(User))
    count = int(result.scalar_one())
    if count > 0:
        return
    logger.info(
        "no users found, creating default admin '%s'", settings.admin_username
    )
    await create_user(
        db,
        username=settings.admin_username,
        password=settings.admin_password,
        role="admin",
    )