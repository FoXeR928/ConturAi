from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.core.exceptions import AppError  # <-- ДОБАВЛЕН ИМПОРТ
from app.db.models import User
from app.db.session import get_session
from app.schemas import ChatCreate, MessageIn, ChatRename
from app.services import chat_service, download_service

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
    await chat_service.rename_chat(session, user, chat_id, payload.name)
    return {"result": True, "message": "Чат переименован"}

@router.get("/get")
async def get_chats(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
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
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int | None = None,
    offset: int = 0,
):
    name, messages, total = await chat_service.get_messages(
        session, user, chat_id, limit=limit, offset=offset
    )
    
    return {
        "result": True,
        "chat_name": name,
        "messages_history": messages,
        "total": total,
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
    await chat_service.soft_delete_chat(session, user, chat_id)
    return {"result": True, "message": "Чат удален", "category": "success"}

@router.get("/delete/irrevocably/get")
async def get_deleted(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
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
    # Проверяем доступ
    if not await download_service.check_access(session, user, chat_id=chat_id):
        raise AppError("Нет доступа. Запросите разрешение у администратора.", "warning", 403)

    # Распаковываем ТРИ значения (total нам здесь не нужен)
    name, messages, _ = await chat_service.get_messages(session, user, chat_id)
    
    lines = [f"# {name}\n"]
    for msg in messages:
        role = "Пользователь" if msg["chat_role"] == "user" else "Ассистент"
        lines.append(f"**{role}:**\n{msg['text']}\n")
    
    md_content = "\n".join(lines)
    
    return StreamingResponse(
        iter([md_content]),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=chat_{chat_id}.md"}
    )