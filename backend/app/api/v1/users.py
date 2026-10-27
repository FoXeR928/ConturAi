from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas import RegistrationUser, UpdatePassword, UpdateRole, UpdateStatus
from app.services import user_service

router = APIRouter()

# ==============================================================================
# БЛОК 1: ИНФОРМАЦИЯ О ТЕКУЩЕМ ПОЛЬЗОВАТЕЛЕ
# ==============================================================================

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """
    Получение данных о текущем авторизованном пользователе.
    
    Фронтенд вызывает этот эндпоинт после логина, чтобы узнать:
    - Свой логин и отображаемое имя.
    - Свою роль (чтобы понять, показывать ли кнопку "Администрирование").
    """
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
    """
    Получение списка всех пользователей системы.
    
    По умолчанию показывает только активных. Если передан параметр 
    `include_deleted=True`, вернет также пользователей из "корзины" 
    (тех, у кого логин изменен на `_deleted_...`).
    """
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
    """
    Регистрация нового пользователя администратором.
    
    Принимает логин, имя, пароль и роль (admin / user / editor).
    Хэширует пароль и сохраняет пользователя в БД.
    """
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
    """
    Смена пароля.
    
    Доступно любому авторизованному пользователю (для смены своего пароля), 
    а также администратору (для сброса пароля любому сотруднику).
    Проверка прав происходит внутри сервиса.
    """
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
    """
    Изменение роли пользователя (повышение до админа или понижение до юзера/редактора).
    
    Сервис защищает от сценария, когда администратор случайно понижает 
    права последнему оставшемуся админу в системе.
    """
    await user_service.update_role(session, actor, payload.login, payload.role)
    return {"result": True, "message": "Роль изменена", "category": "success"}


@router.patch("/change/status")
async def change_status(
    payload: UpdateStatus,
    actor: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Блокировка или разблокировка пользователя.
    
    Если `disabled=True`, пользователь не сможет войти (даже с верным паролем).
    Сервис также защищает от блокировки последнего администратора.
    """
    await user_service.update_user_status(session, actor, payload.login, payload.disabled)
    action = "заблокирован" if payload.disabled else "разблокирован"
    return {"result": True, "message": f"Пользователь {action}", "category": "success"}


# ==============================================================================
# БЛОК 6: УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ (МЯГКОЕ И БЕЗВОЗВРАТНОЕ)
# ==============================================================================

@router.delete("/delete")
async def delete_user(
    login: str,
    actor: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Мягкое удаление пользователя (в корзину).
    
    Аккаунт не стирается из базы физически. Вместо этого пользователь 
    блокируется, а его логин переименовывается (добавляется суффикс `_deleted_...`), 
    чтобы освободить исходный логин для регистрации нового сотрудника.
    """
    await user_service.delete_user(session, actor, login)
    return {"result": True, "message": "Пользователь удален", "category": "success"}


@router.delete("/purge")
async def purge_user(
    login: str,
    actor: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Полное (безвозвратное) удаление пользователя из базы данных.
    
    Удаляет запись пользователя и каскадно стирает все его чаты и сообщения. 
    Применяется к пользователям, которые уже находятся в корзине (`_deleted_`).
    """
    await user_service.purge_user(session, actor, login)
    return {"result": True, "message": "Пользователь удален навсегда", "category": "success"}