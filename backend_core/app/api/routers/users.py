from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas import RegistrationUser, UpdatePassword, UpdateRole, UpdateStatus, UpdateUserName
from app.services import user_service

router = APIRouter()

# ==============================================================================
# БЛОК 1: ИНФОРМАЦИЯ О ТЕКУЩЕМ ПОЛЬЗОВАТЕЛЕ
# ==============================================================================

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Данные о текущем авторизованном пользователе."""
    return {
        "result": True,
        "login": user.login,
        "user_name": user.user_name,
        "role": user.role
    }


# ==============================================================================
# БЛОК 2: ПРОСМОТР СПИСКА ПОЛЬЗОВАТЕЛЕЙ (ТОЛЬКО АДМИН)
# ==============================================================================

@router.get("/get")
async def get_users(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
    include_deleted: bool = False,
):
    """Получение списка всех пользователей (опционально с удаленными)."""
    return {
        "result": True,
        "users": await user_service.list_users(session, include_deleted=include_deleted),
        "message": "Пользователи получены",
        "category": "success",
    }


# ==============================================================================
# БЛОК 3: СОЗДАНИЕ НОВОГО ПОЛЬЗОВАТЕЛЯ (ТОЛЬКО АДМИН)
# ==============================================================================

@router.post("/registration")
async def registration(
    payload: RegistrationUser,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """Регистрация нового пользователя администратором."""
    await user_service.create_user(
        session, payload.login, payload.user_name, payload.password, payload.role
    )
    return {"result": True, "message": "Пользователь создан", "category": "success"}


# ==============================================================================
# БЛОК 4: ИЗМЕНЕНИЕ ПАРОЛЯ
# ==============================================================================

@router.patch("/change/password")
async def change_password(
    payload: UpdatePassword,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Смена пароля (своего или чужого, если админ)."""
    await user_service.update_password(session, user, payload.login, payload.password)
    return {"result": True, "message": "Пароль изменен", "category": "success"}


# ==============================================================================
# БЛОК 5: УПРАВЛЕНИЕ РОЛЯМИ И СТАТУСОМ (ТОЛЬКО АДМИН)
# ==============================================================================

@router.patch("/change/role")
async def change_role(
    payload: UpdateRole,
    actor: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """Изменение роли пользователя."""
    await user_service.update_role(session, actor, payload.login, payload.role)
    return {"result": True, "message": "Роль изменена", "category": "success"}


@router.patch("/change/status")
async def change_status(
    payload: UpdateStatus,
    actor: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """Блокировка или разблокировка пользователя."""
    await user_service.update_user_status(session, actor, payload.login, payload.disabled)
    action = "заблокирован" if payload.disabled else "разблокирован"
    return {"result": True, "message": f"Пользователь {action}", "category": "success"}

@router.patch("/change/name")
async def change_name(
    payload: UpdateUserName,
    actor: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """Смена отображаемого имени."""
    await user_service.update_user_name(session, actor, payload.login, payload.user_name)
    return {"result": True, "message": "Имя пользователя изменено", "category": "success"}


# ==============================================================================
# БЛОК 6: УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ (МЯГКОЕ И БЕЗВОЗВРАТНОЕ)
# ==============================================================================

@router.delete("/delete")
async def delete_user(
    login: str,
    actor: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """Мягкое удаление (в корзину)."""
    await user_service.delete_user(session, actor, login)
    return {"result": True, "message": "Пользователь удален", "category": "success"}


@router.delete("/purge")
async def purge_user(
    login: str,
    actor: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """Полное удаление из БД."""
    await user_service.purge_user(session, actor, login)
    return {"result": True, "message": "Пользователь удален навсегда", "category": "success"}