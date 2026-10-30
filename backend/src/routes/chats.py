from __future__ import annotations

import json
import logging
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, get_registry
from ..models import User
from ..schemas import (
    ChatRoomCreate,
    ChatRoomRead,
    MessageCreate,
    MessageRead,
)
from ..services import chat_service
from ..services.plugin_loader import PluginRegistry

logger = logging.getLogger("conturai.backend.chats")

router = APIRouter(prefix="/api/chats", tags=["chats"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# ---- Комнаты ---------------------------------------------------------------

@router.get("", response_model=list[ChatRoomRead])
async def list_rooms(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.list_rooms(db, user.id)


@router.post("", response_model=ChatRoomRead, status_code=201)
async def create_room(
    payload: ChatRoomCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.create_room(db, user.id, payload.title)


@router.get("/{room_id}", response_model=ChatRoomRead)
async def get_room(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    room = await chat_service.get_room(db, room_id, user.id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.delete("/{room_id}", status_code=204)
async def delete_room(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    room = await chat_service.get_room(db, room_id, user.id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    await db.delete(room)
    await db.commit()
    return None


# ---- Сообщения -------------------------------------------------------------

@router.get("/{room_id}/messages", response_model=list[MessageRead])
async def list_messages(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    room = await chat_service.get_room(db, room_id, user.id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return await chat_service.list_messages(db, room_id)


# ---- SSE-стрим -------------------------------------------------------------

@router.post("/{room_id}/messages/stream")
async def stream_message(
    room_id: uuid.UUID,
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    registry: PluginRegistry = Depends(get_registry),
):
    room = await chat_service.get_room(db, room_id, user.id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    provider = registry.get_inference_provider()
    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="No active inference provider — activate an LLM plugin in admin",
        )

    # Сохраняем сообщение пользователя
    await chat_service.save_user_message(db, room_id, payload.content)

    # Загружаем историю ДО старта стрима (в той же сессии)
    history_rows = await chat_service.list_messages(db, room_id)
    messages = chat_service.messages_to_chat(history_rows)

    # Прогоняем контекст через общий pipeline активных плагинов
    pipeline = registry.build_context_pipeline()
    processed = await pipeline.run(messages, room_id=str(room_id))

    # Открываем НЕЗАВИСИМУЮ сессию внутри генератора (не держим FastAPI Depends)
    async def generator() -> AsyncIterator[str]:
        full_response = ""
        try:
            async for token in provider.stream(processed):
                full_response += token
                yield _sse("token", {"token": token})
        except Exception as exc:
            logger.exception("streaming error")
            yield _sse("error", {"error": str(exc)})
            return

        msg_id = None
        if full_response:
            try:
                msg_id = await chat_service.save_assistant_message(
                    room_id, full_response
                )
            except Exception as exc:
                logger.warning("failed to persist assistant message: %s", exc)

        yield _sse(
            "done",
            {
                "message_id": str(msg_id) if msg_id else None,
                "length": len(full_response),
            },
        )

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )