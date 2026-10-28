from fastapi import APIRouter

# ==============================================================================
# БЛОК 1: ИМПОРТ ВСЕХ МОДУЛЕЙ С ЭНДПОИНТАМИ (ИЗ ПАПКИ V1)
# ==============================================================================

# Здесь мы импортируем все файлы, в которых описаны роутеры для разных частей системы.
# Каждый из этих модулей содержит свой APIRouter и набор @router.get/post/... функций.
from app.api.v1 import (
    ai,          # Генерация ответов, работа с документами (upload, parse, delete)
    auth,        # Логин и логаут
    chats,       # Создание чатов, история сообщений, корзина
    health,      # Проверка статуса системы (healthcheck)
    llm_configs, # Динамические настройки нейросети (температура, токены и т.д.)
    prompts,     # Управление системными промптами
    users,       # Управление пользователями (роли, блокировки)
    system,      # Мониторинг ресурсов (CPU, RAM, GPU) и бэкапы
    downloads,   # Запросы на скачивание файлов (права доступа)
    audit,       # Журнал действий пользователей (логи)
    few_shots,   # Примеры "вопрос-ответ" для обучения промптов
    tags         # Справочник тегов для фильтрации
)

# ==============================================================================
# БЛОК 2: СОЗДАНИЕ ГЛАВНОГО РОУТЕРА
# ==============================================================================

# Создаем корневой роутер, в который будем "вкладывать" все остальные.
# В итоге этот api_router будет подключен в главном файле main.py к приложению FastAPI.
api_router = APIRouter()

# ==============================================================================
# БЛОК 3: РЕГИСТРАЦИЯ ПОДМОДУЛЕЙ (ПОДКЛЮЧЕНИЕ ЭНДПОИНТОВ)
# ==============================================================================

# Метод include_router берет роутер из модуля и добавляет его к общему.
# Параметр prefix="/..." добавляет обязательную часть URL ко всем эндпоинтам модуля.
# Параметр tags=["..."] группирует эндпоинты в Swagger UI (/docs) для удобства.

# 1. Healthcheck. Подключен БЕЗ префикса, поэтому доступен по корню (например, /status).
api_router.include_router(health.router)

# 2. Авторизация. Все эндпоинты будут по пути /auth/... (например, /auth/login).
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# 3. Чаты и сообщения. Путь /chats/... (например, /chats/create).
api_router.include_router(chats.router, prefix="/chats", tags=["Chats"])

# 4. Пользователи. Путь /users/... (например, /users/get).
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# 5. Промпты. Путь /prompts/...
api_router.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])

# 6. Параметры LLM. Путь /llm-configs/...
api_router.include_router(llm_configs.router, prefix="/llm-configs", tags=["LLM Configs"])

# 7. Основной модуль ИИ. Путь /ai/... (например, /ai/messages/create, /ai/docs/upload).
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])

# 8. Few-Shot примеры. Путь /few-shots/...
api_router.include_router(few_shots.router, prefix="/few-shots", tags=["Few Shots"])

# 9. Системный мониторинг и бэкапы. Путь /system/...
api_router.include_router(system.router, prefix="/system", tags=["System"])

# 10. Запросы на скачивание. Путь /downloads/...
api_router.include_router(downloads.router, prefix="/downloads", tags=["Download"])

# 11. Аудит (логи). Путь /audit/...
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])

# 12. Справочник тегов. Путь /tags/...
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])