from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth.deps import get_current_user
from app.schemas.chat import (
    ChatCreateRequest,
    ChatOut,
    MessageOut,
    SendMessageRequest,
    SendMessageResponse,
)
from app.schemas.plugin import ChatMessage


router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get("", response_model=list[ChatOut])
async def list_chats(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> list[ChatOut]:
    chat_store = request.app.state.chat_store
    rows = await chat_store.list_for_user(user["id"])
    return [ChatOut(**row) for row in rows]


@router.post("", response_model=ChatOut, status_code=201)
async def create_chat(
    payload: ChatCreateRequest,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> ChatOut:
    chat_store = request.app.state.chat_store
    chat_id = await chat_store.create(user["id"], payload.title)
    return ChatOut(id=chat_id, title=payload.title, created_at="")


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> None:
    chat_store = request.app.state.chat_store
    ok = await chat_store.delete(chat_id, user["id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Чат не найден")


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
async def list_messages(
    chat_id: str,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> list[MessageOut]:
    chat_store = request.app.state.chat_store
    chat = await chat_store.get(chat_id, user["id"])
    if chat is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    rows = await chat_store.list_messages(chat_id)
    return [MessageOut(**row) for row in rows]


@router.post("/{chat_id}/messages", response_model=SendMessageResponse)
async def send_message(
    chat_id: str,
    payload: SendMessageRequest,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> SendMessageResponse:
    chat_store = request.app.state.chat_store
    registry = request.app.state.registry

    chat = await chat_store.get(chat_id, user["id"])
    if chat is None:
        raise HTTPException(status_code=404, detail="Чат не найден")

    plugin = registry.get(payload.plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Плагин не найден")
    if not plugin.get_manifest().is_active:
        raise HTTPException(status_code=409, detail="Плагин отключен")

    history_rows = await chat_store.list_messages(chat_id, limit=20)
    history = [
        ChatMessage(role=row["role"], content=row["content"])
        for row in history_rows
        if row["role"] in ("user", "assistant", "system")
    ]

    user_msg_id = await chat_store.add_message(
        chat_id, "user", payload.content,
    )

    try:
        answer = await plugin.execute(payload.content, history)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Ошибка плагина: {exc}",
        ) from exc

    assistant_msg_id = await chat_store.add_message(
        chat_id, "assistant", answer,
    )

    return SendMessageResponse(
        user_message=MessageOut(
            id=user_msg_id, role="user",
            content=payload.content, created_at="",
        ),
        assistant_message=MessageOut(
            id=assistant_msg_id, role="assistant",
            content=answer, created_at="",
        ),
    )