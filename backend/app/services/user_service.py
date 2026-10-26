import time
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.secrets import create_access_token
from app.db.models import User
from app.services import llm_config_service


async def authenticate(
    session: AsyncSession,
    login: str,
    password: str,
    long_lived: bool = False,
) -> str:
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    if not user or not user.check_password(password):
        raise AppError("Неверный логин или пароль", "warning", 401)

    jwt_cfg = await llm_config_service.get_jwt(session)
    return create_access_token(
        login,
        long_lived=long_lived,
        minutes=jwt_cfg["minutes"],
        days=jwt_cfg["days"],
    )

async def list_users(session: AsyncSession, include_deleted: bool = False) -> list[dict]:
    stmt = select(
        User.login,
        User.user_name,
        User.is_admin,
        User.disabled,
        User.created_at,
        User.updated_at,
    ).where(User.is_system.is_(False))

    if not include_deleted:
        stmt = stmt.where(~User.login.contains("_deleted_"))
    
    result = await session.execute(stmt)
    return [dict(row._mapping) for row in result.all()]



async def create_user(
    session: AsyncSession, login: str, user_name: str, password: str
) -> None:
    exists = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    if exists:
        raise AppError("Пользователь уже создан", "warning", 409)
    user = User(login=login, user_name=user_name, role=role)
    user.set_password(password)
    session.add(user)
    await session.commit()


async def update_password(
    session: AsyncSession, actor: User, login: str, password: str
) -> None:
    if actor.login != login and not actor.is_admin:
        raise AppError("Нет доступа", "warning", 403)
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    if not user:
        raise AppError("Не найден пользователь", "warning", 404)
    user.set_password(password)
    await session.commit()


async def _admins_count(session: AsyncSession) -> int:
    return (
        await session.execute(
            select(func.count(User.login)).where(User.role == "admin")
        )
    ).scalar_one()


async def update_role(
    session: AsyncSession, actor: User, login: str, role: str
) -> None:
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    if not user:
        raise AppError("Не найден пользователь", "warning", 404)
        
    if user.is_admin and role != "admin":
        if await _admins_count(session) <= 1:
            raise AppError(
                "Нельзя изменить роль из-за отсутствия других администраторов",
                "warning",
                403,
            )
            
    await session.execute(
        update(User).where(User.login == login).values(role=role)
    )
    await session.commit()


async def update_user_status(
    session: AsyncSession, actor: User, login: str, disabled: bool
) -> None:
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    if not user:
        raise AppError("Не найден пользователь", "warning", 404)
    
    if user.is_admin and disabled:
        if await _admins_count(session) <= 1:
            raise AppError("Нельзя заблокировать последнего администратора", "warning", 403)
            
    user.disabled = disabled
    await session.commit()


async def delete_user(session: AsyncSession, actor: User, login: str) -> None:
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    
    if not user:
        raise AppError("Не найден пользователь", "warning", 404)
        
    # Защита от повторного удаления
    if "_deleted_" in user.login:
        raise AppError("Пользователь уже удален", "warning", 400)

    if user.is_admin and await _admins_count(session) <= 1:
        raise AppError("Нельзя удалить последнего администратора", "warning", 403)

    # Мягкое удаление: блокируем и меняем логин
    user.disabled = True
    user.login = f"{login}_deleted_{int(time.time())}" 
    
    await session.commit()

async def purge_user(session: AsyncSession, actor: User, login: str) -> None:
    """Безвозвратное удаление пользователя из БД"""
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    
    if not user:
        raise AppError("Не найден пользователь", "warning", 404)

    if user.is_admin and await _admins_count(session) <= 1:
        raise AppError("Нельзя удалить последнего администратора", "warning", 403)

    await session.execute(delete(User).where(User.login == login))
    await session.commit()