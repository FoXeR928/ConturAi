import time
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.secrets import create_access_token
from app.db.models import User

# ==============================================================================
# БЛОК 1: АУТЕНТИФИКАЦИЯ (ВХОД В СИСТЕМУ)
# ==============================================================================

async def authenticate(
    session: AsyncSession,
    login: str,
    password: str,
    long_lived: bool = False,
) -> str:
    """
    Проверяет логин и пароль. Возвращает JWT.
    Время жизни токена берется из настроек ядра (config.py).
    """
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    
    if not user or not user.check_password(password):
        raise AppError("Неверный логин или пароль", "warning", 401)

    # Генерируем токен, используя стандартные настройки из config.py
    return create_access_token(
        login,
        long_lived=long_lived,
        minutes=settings.token_expire_minutes,
        days=settings.token_expire_days,
    )


# ==============================================================================
# БЛОК 2: ЧТЕНИЕ СПИСКА ПОЛЬЗОВАТЕЛЕЙ
# ==============================================================================

async def list_users(session: AsyncSession, include_deleted: bool = False) -> list[dict]:
    """
    Возвращает список пользователей для админ-панели.
    Скрывает системного пользователя и удаленных (если не запрошено обратное).
    """
    stmt = select(
        User.login,
        User.user_name,
        User.role,
        User.disabled,
        User.created_at,
        User.updated_at,
    ).where(User.is_system.is_(False))

    if not include_deleted:
        stmt = stmt.where(~User.login.contains("_deleted_"))
    
    result = await session.execute(stmt)
    return [dict(row._mapping) for row in result.all()]


# ==============================================================================
# БЛОК 3: СОЗДАНИЕ НОВОГО ПОЛЬЗОВАТЕЛЯ
# ==============================================================================

async def create_user(
    session: AsyncSession, login: str, user_name: str, password: str, role: str = "user"
) -> None:
    """
    Создает нового пользователя. Проверяет, что логин не занят.
    """
    exists = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    if exists:
        raise AppError("Пользователь уже создан", "warning", 409)
        
    user = User(login=login, user_name=user_name, role=role)
    user.set_password(password)
    session.add(user)
    await session.commit()


# ==============================================================================
# БЛОК 4: СМЕНА ПАРОЛЯ
# ==============================================================================

async def update_password(
    session: AsyncSession, actor: User, login: str, password: str
) -> None:
    """
    Смена пароля. Пользователь меняет свой, админ — любому.
    """
    if actor.login != login and not actor.is_admin:
        raise AppError("Нет доступа", "warning", 403)
        
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    if not user:
        raise AppError("Не найден пользователь", "warning", 404)
        
    user.set_password(password)
    await session.commit()


# ==============================================================================
# БЛОК 5: УПРАВЛЕНИЕ РОЛЯМИ И СТАТУСОМ (ЗАЩИТА ОТ БЛОКИРОВКИ СИСТЕМЫ)
# ==============================================================================

async def _admins_count(session: AsyncSession) -> int:
    """Считает количество активных администраторов в системе."""
    return (
        await session.execute(
            select(func.count(User.login)).where(User.role == "admin")
        )
    ).scalar_one()


async def update_role(
    session: AsyncSession, actor: User, login: str, role: str
) -> None:
    """
    Изменение роли. Запрещает понижать последнего администратора.
    """
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
    """
    Блокировка/разблокировка. Запрещает блокировать последнего админа.
    """
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


async def update_user_name(
    session: AsyncSession, actor: User, login: str, new_name: str
) -> None:
    """Смена отображаемого имени."""
    if actor.login != login and not actor.is_admin:
        raise AppError("Нет доступа", "warning", 403)
        
    user = (await session.execute(select(User).where(User.login == login))).scalar_one_or_none()
    if not user:
        raise AppError("Не найден пользователь", "warning", 404)
        
    user.user_name = new_name
    await session.commit()


# ==============================================================================
# БЛОК 6: УДАЛЕНИЕ (МЯГКОЕ И БЕЗВОЗВРАТНОЕ)
# ==============================================================================

async def delete_user(session: AsyncSession, actor: User, login: str) -> None:
    """
    Мягкое удаление (в корзину). Переименовывает логин и блокирует пользователя.
    """
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    
    if not user:
        raise AppError("Не найден пользователь", "warning", 404)
        
    if "_deleted_" in user.login:
        raise AppError("Пользователь уже удален", "warning", 400)

    if user.is_admin and await _admins_count(session) <= 1:
        raise AppError("Нельзя удалить последнего администратора", "warning", 403)

    user.disabled = True
    user.login = f"{login}_deleted_{int(time.time())}" 
    await session.commit()


async def purge_user(session: AsyncSession, actor: User, login: str) -> None:
    """
    Полное удаление пользователя из БД (каскадно удалит его чаты и сообщения).
    """
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    
    if not user:
        raise AppError("Не найден пользователь", "warning", 404)

    if user.is_admin and await _admins_count(session) <= 1:
        raise AppError("Нельзя удалить последнего администратора", "warning", 403)

    await session.execute(delete(User).where(User.login == login))
    await session.commit()