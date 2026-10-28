import time
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.secrets import create_access_token
from app.db.models import User
from app.services import llm_config_service

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
    Проверяет логин и пароль пользователя. 
    Если данные верны — генерирует и возвращает JWT-токен.
    
    Время жизни токена (короткое или долгое) берется из настроек в БД 
    (llm_config_service.get_jwt), чтобы администратор мог менять его на лету.
    """
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    
    # Проверка пароля происходит внутри метода check_password (там же проверка на блокировку)
    if not user or not user.check_password(password):
        raise AppError("Неверный логин или пароль", "warning", 401)

    # Получаем настройки времени жизни токена из БД
    jwt_cfg = await llm_config_service.get_jwt(session)
    
    # Генерируем токен
    return create_access_token(
        login,
        long_lived=long_lived,
        minutes=jwt_cfg["minutes"],
        days=jwt_cfg["days"],
    )


# ==============================================================================
# БЛОК 2: ЧТЕНИЕ СПИСКА ПОЛЬЗОВАТЕЛЕЙ
# ==============================================================================

async def list_users(session: AsyncSession, include_deleted: bool = False) -> list[dict]:
    """
    Возвращает список пользователей для админ-панели.
    
    - Системный пользователь (SYSTEM_LOGIN) скрыт из списка (is_system == False).
    - По умолчанию мягко удаленные пользователи (с суффиксом `_deleted_` в логине) скрыты.
    - Если передан `include_deleted=True` (корзина), они также попадают в выборку.
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
    Создает нового пользователя (вызывается админом).
    Проверяет, что логин не занят, хэширует пароль и сохраняет в БД.
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
    Смена пароля. 
    Пользователь может менять свой пароль. Админ может менять пароль любому.
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
    """
    Вспомогательная функция: считает количество активных администраторов в системе.
    Нужна для защиты от случайного "запирания" системы (когда нет ни одного админа).
    """
    return (
        await session.execute(
            select(func.count(User.login)).where(User.role == "admin")
        )
    ).scalar_one()


async def update_role(
    session: AsyncSession, actor: User, login: str, role: str
) -> None:
    """
    Изменение роли пользователя (например, с user на editor или admin).
    
    ЗАЩИТА: Если мы понижаем роль пользователю, который является администратором, 
    и в системе больше нет других админов, мы выбрасываем ошибку.
    """
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    if not user:
        raise AppError("Не найден пользователь", "warning", 404)
        
    # Если у пользователя была роль admin, а новая роль — нет
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
    Блокировка или разблокировка пользователя.
    
    ЗАЩИТА: Запрещает блокировать последнего оставшегося администратора.
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
    Мягкое удаление пользователя (в корзину).
    
    Что происходит:
    1. Пользователь блокируется (disabled = True).
    2. К его логину добавляется суффикс `_deleted_{timestamp}`.
    
    Это освобождает исходный логин (например, "ivanov"), чтобы 
    на его место можно было принять нового сотрудника, 
    но при этом старые чаты и историю не приходится удалять.
    """
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

    user.disabled = True
    user.login = f"{login}_deleted_{int(time.time())}" 
    await session.commit()


async def purge_user(session: AsyncSession, actor: User, login: str) -> None:
    """
    Безвозвратное (полное) удаление пользователя из БД.
    Обычно вызывается для пользователей, которые уже находятся в корзине.
    
    ВНИМАНИЕ: Вместе с пользователем удалятся все его чаты и сообщения (каскадно).
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