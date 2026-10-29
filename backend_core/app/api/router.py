from fastapi import APIRouter

# ==============================================================================
# БЛОК 1: ИМПОРТ БАЗОВЫХ МОДУЛЕЙ ЯДРА
# ==============================================================================

from app.api.v1 import (
    auth,        # Логин и логаут
    chats,       # Создание чатов, история сообщений, корзина
    health,      # Проверка статуса системы (healthcheck)
    users,       # Управление пользователями (роли, блокировки)
    plugins,     # API для получения списка активных плагинов (для фронтенда)
)

# ==============================================================================
# БЛОК 2: СОЗДАНИЕ ГЛАВНОГО РОУТЕРА
# ==============================================================================

api_router = APIRouter()

# ==============================================================================
# БЛОК 3: РЕГИСТРАЦИЯ БАЗОВЫХ ЭНДПОИНТОВ
# ==============================================================================

# 1. Healthcheck (доступен по корню, например /status)
api_router.include_router(health.router)

# 2. Авторизация (/auth/login, /auth/logout)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# 3. Чаты и сообщения (/chats/create, /chats/messages/get и т.д.)
api_router.include_router(chats.router, prefix="/chats", tags=["Chats"])

# 4. Пользователи (/users/get, /users/change/role и т.д.)
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# 5. Управление плагинами (/plugins/list, /plugins/toggle)
api_router.include_router(plugins.router, prefix="/plugins", tags=["Plugins"])