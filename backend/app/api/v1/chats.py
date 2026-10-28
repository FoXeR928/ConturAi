from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas import ChatCreate, MessageIn, ChatRename
from app.services import chat_service

router = APIRouter()

# ==============================================================================
# БЛОК 1: УПРАВЛЕНИЕ ЧАТАМИ (СОЗДАНИЕ, ПЕРЕИМЕНОВАНИЕ, СПИСОК)
# ==============================================================================

@router.post("/create")
async def create_chat(
    payload: ChatCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Создание нового пустого чата.
    Привязывается к текущему авторизованному пользователю.
    """
    chat_id = await chat_service.create_chat(session, user, payload.name)
    return {
        "result": True,
        "chat_id": chat_id,
        "message": "Чат создан",
        "category": "success",
    }

@router.patch("/rename")
async def rename_chat(
    chat_id: UUID,
    payload: ChatRename,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Переименование существующего чата.
    Проверяет, что чат принадлежит этому пользователю (или он админ).
    """
    await chat_service.rename_chat(session, user, chat_id, payload.name)
    return {"result": True, "message": "Чат переименован"}

@router.get("/get")
async def get_chats(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Получение списка всех активных (не удаленных) чатов пользователя.
    Используется для отрисовки боковой панели (сайдбара).
    """
    return {
        "result": True,
        "chats": await chat_service.list_chats(session, user),
        "message": "Чаты получены",
        "category": "success",
    }


# ==============================================================================
# БЛОК 2: РАБОТА С СООБЩЕНИЯМИ ВНУТРИ ЧАТА
# ==============================================================================

@router.get("/messages/get")
async def get_messages(
    chat_id: UUID,
    limit: int | None = None,
    offset: int = 0,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Загрузка истории сообщений для конкретного чата.
    Возвращает название чата и массив сообщений (с ролями 'user' и 'assistant').
    """
    name, messages = await chat_service.get_messages(session, user, chat_id)
    return {
        "result": True,
        "chat_name": name,
        "messages_history": messages,
        "total_count": total
        "message": "Сообщения получены",
        "category": "success",
    }

@router.post("/messages/create")
async def create_message(
    chat_id: UUID,
    payload: MessageIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Создание обычного текстового сообщения (без вызова ИИ).
    Обычно используется для системных сообщений или тестирования.
    """
    await chat_service.create_message(session, user, chat_id, payload.text)
    return {
        "result": True,
        "message": "Сообщение создано",
        "category": "success",
    }

@router.delete("/messages/delete")
async def delete_message(
    chat_id: UUID,
    message_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Удаление конкретного сообщения из чата.
    Проверяет права доступа к чату перед удалением.
    """
    await chat_service.delete_message(session, user, chat_id, message_id)
    return {
        "result": True,
        "message": "Сообщение удалено",
        "category": "success",
    }


# ==============================================================================
# БЛОК 3: КОРЗИНА (МЯГКОЕ УДАЛЕНИЕ И ВОССТАНОВЛЕНИЕ)
# ==============================================================================

@router.patch("/delete")
async def delete_chat(
    chat_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Мягкое удаление чата (перемещение в корзину).
    В БД просто ставится флаг is_deleted = True. Сообщения не удаляются.
    """
    await chat_service.soft_delete_chat(session, user, chat_id)
    return {"result": True, "message": "Чат удален", "category": "success"}

@router.get("/delete/irrevocably/get")
async def get_deleted(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Просмотр корзины: список всех мягко удаленных чатов.
    Доступно только администратору.
    """
    return {
        "result": True,
        "chats": await chat_service.list_deleted_chats(session),
        "message": "Чаты на удаление получены",
        "category": "success",
    }

@router.patch("/recovery/list")
async def recovery_list(
    chats: list[UUID],
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Восстановление чатов из корзины.
    Принимает массив UUID чатов. Снимает флаг is_deleted = False.
    Доступно только администратору.
    """
    await chat_service.restore_chats(session, chats)
    return {"result": True, "message": "Чаты восстановлены", "category": "success"}


# ==============================================================================
# БЛОК 4: БЕЗВОЗВРАТНОЕ УДАЛЕНИЕ (АДМИНИСТРАТИВНЫЕ ОПЕРАЦИИ)
# ==============================================================================

@router.delete("/delete/irrevocably/list")
async def purge_deleted(
    chats: list[UUID],
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Безвозвратное удаление конкретных чатов из корзины.
    Физически удаляет записи из БД (каскадно удалятся и сообщения).
    """
    await chat_service.purge_deleted(session, chats)
    return {
        "result": True,
        "message": "Чаты удалены безвозвратно",
        "category": "success",
    }

@router.delete("/delete/irrevocably/all")
async def purge_all_deleted(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Полная очистка корзины (удаление всех мягко удаленных чатов).
    Передает None в сервис, что означает "удалить всё, где is_deleted = True".
    """
    await chat_service.purge_deleted(session, None)
    return {"result": True, "message": "Чаты удалены", "category": "success"}


# ==============================================================================
# БЛОК 5: ЭКСПОРТ (СКАЧИВАНИЕ ИСТОРИИ ЧАТА)
# ==============================================================================

@router.get("/export/{chat_id}")
async def export_chat(
    chat_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Экспорт чата в формате Markdown (.md).
    Проверяет права: админы скачивают свободно, остальные — только с разрешения.
    """
    # 1. Проверяем доступ (админ проходит сразу, остальные ищут одобренную заявку)
    has_access = await download_service.check_access(session, user, chat_id=chat_id)
    if not has_access:
        raise AppError(
            "Скачивание запрещено. Запросите доступ у администратора.",
            "warning",
            403
        )

    # 2. Генерируем Markdown
    name, messages = await chat_service.get_messages(session, user, chat_id)
    
    lines = [f"# {name}\n"]
    for msg in messages:
        role = "Пользователь" if msg["chat_role"] == "user" else "Ассистент"
        lines.append(f"**{role}:**\n{msg['text']}\n")
    
    md_content = "\n".join(lines)
    
    return StreamingResponse(
        iter([md_content]),
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=chat_{chat_id}.md"
        }
    )