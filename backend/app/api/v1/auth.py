from fastapi import APIRouter, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.services import user_service

router = APIRouter()

# ==============================================================================
# БЛОК 1: АВТОРИЗАЦИЯ (ВХОД В СИСТЕМУ)
# ==============================================================================

@router.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    expires_use: bool = Form(False),
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для входа в систему.
    
    Особенности:
    1. Использует OAuth2PasswordRequestForm. Это значит, что фронтенд должен отправлять 
       данные не в JSON, а как `application/x-www-form-urlencoded` (поля `username` и `password`).
       Это стандарт FastAPI, который позволяет кнопке "Authorize" в Swagger UI (/docs) работать из коробки.
    2. Принимает дополнительный параметр `expires_use` (чекбокс "Запомнить меня"). 
       Если он True, `user_service` сгенерирует долгоживущий токен (например, на 7 дней), 
       иначе — короткоживущий (например, на 30 минут).
    """
    
    # Вызываем сервис аутентификации.
    # Внутри него происходит:
    # - Поиск пользователя в БД по логину.
    # - Проверка пароля (bcrypt).
    # - Проверка, не заблокирован ли пользователь (disabled).
    # - Генерация JWT-токена с нужным временем жизни.
    token = await user_service.authenticate(
        session, form.username, form.password, long_lived=expires_use
    )
    
    # Возвращаем токен. Фронтенд сохранит его в localStorage.
    return {
        "result": True,
        "access_token": token,
        "token_type": "bearer",
        "message": "Авторизация прошла успешно",
        "category": "success",
    }


# ==============================================================================
# БЛОК 2: ДЕАВТОРИЗАЦИЯ (ВЫХОД ИЗ СИСТЕМЫ)
# ==============================================================================

@router.post("/logout")
async def logout(_: User = Depends(get_current_user)):
    """
    Эндпоинт для выхода из системы.
    
    Поскольку мы используем JWT (JSON Web Tokens), они являются stateless (без сохранения состояния).
    Это значит, что сервер не хранит сессию пользователя. Чтобы "разлогинить" пользователя, 
    серверу на самом деле ничего делать не нужно.
    
    Единственная задача этого эндпоинта:
    1. Проверить, что запрос делает авторизованный пользователь (через Depends(get_current_user)).
       Это защищает от спама неавторизованных запросов на этот URL.
    2. Вернуть успешный ответ. Фронтенд, получив его, просто удаляет токен из localStorage.
    """
    
    return {
        "result": True,
        "message": "Пользователь деавторизирован",
        "category": "success",
    }