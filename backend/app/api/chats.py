from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.auth.deps import get_current_user
from app.core.config import settings
from app.core.errors import ApiError
from app.core.ratelimit import limiter
from app.schemas.chat import (
    ChatCreateRequest,
    ChatOut,
    MessageOut,
    SendMessageRequest,
    SendMessageResponse,
)
from app.schemas.plugin import ChatMessage


router = APIRouter(prefix="/api/v1/chats", tags=["chats"])


async def _build_history(
    chat_store: Any, chat_id: str, max_chars: int,
) -> list[ChatMessage]:
    rows = await chat_store.list_messages(chat_id, limit=200)
    history: list[ChatMessage] = []
    total = 0
    for row in reversed(rows):
        if row["role"] not in ("user", "assistant", "system"):
            continue
        content = row["content"]
        if total + len(content) > max_chars:
            break
        history.append(ChatMessage(role=row["role"], content=content))
        total += len(content)
    history.reverse()
    return history


@router.get("", response_model=list[ChatOut])
async def list_chats(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> list[ChatOut]:
    store = request.app.state.chat_store
    return [ChatOut(**r) for r in await store.list_for_user(user["id"])]


@router.post("", response_model=ChatOut, status_code=201)
async def create_chat(
    payload: ChatCreateRequest,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> ChatOut:
    store = request.app.state.chat_store
    chat_id = await store.create(user["id"], payload.title)
    return ChatOut(id=chat_id, title=payload.title, created_at="")


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> None:
    store = request.app.state.chat_store
    if not await store.delete(chat_id, user["id"]):
        raise ApiError("NOT_FOUND", "Чат не найден", status=404)


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
async def list_messages(
    chat_id: str,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> list[MessageOut]:
    store = request.app.state.chat_store
    if await store.get(chat_id, user["id"]) is None:
        raise ApiError("NOT_FOUND", "Чат не найден", status=404)
    return [MessageOut(**r) for r in await store.list_messages(chat_id)]


def _check_plugin(registry: Any, plugin_id: str) -> Any:
    plugin = registry.get(plugin_id)
    if plugin is None:
        raise ApiError("NOT_FOUND", "Плагин не найден", status=404)
    manifest = plugin.get_manifest()
    if not manifest.is_active:
        raise ApiError("PLUGIN_INACTIVE", "Плагин отключен", status=409)
    return plugin


@router.post("/{chat_id}/messages", response_model=SendMessageResponse)
async def send_message(
    chat_id: str,
    payload: SendMessageRequest,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> SendMessageResponse:
    chat_store = request.app.state.chat_store
    registry = request.app.state.registry

    limiter.hit(
        f"msg:{user['id']}",
        settings.message_rate_limit,
        settings.message_window_seconds,
    )

    if await chat_store.get(chat_id, user["id"]) is None:
        raise ApiError("NOT_FOUND", "Чат не найден", status=404)
    plugin = _check_plugin(registry, payload.plugin_id)
    manifest = plugin.get_manifest()

    lock = registry.get_chat_lock(chat_id)
    async with lock:
        history = await _build_history(
            chat_store, chat_id, manifest.max_history_chars,
        )
        user_msg_id = await chat_store.add_message(
            chat_id, "user", payload.content,
        )
        sem = registry.get_semaphore(payload.plugin_id)
        async with sem:
            try:
                answer = await asyncio.wait_for(
                    plugin.execute(payload.content, history),
                    timeout=float(manifest.execution_timeout),
                )
            except asyncio.TimeoutError:
                raise ApiError(
                    "PLUGIN_TIMEOUT", "Плагин не ответил вовремя", status=504,
                ) from None
            except Exception as exc:
                raise ApiError(
                    "PLUGIN_ERROR", f"Ошибка плагина: {exc}", status=502,
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


@router.post("/{chat_id}/messages/stream")
async def stream_message(
    chat_id: str,
    payload: SendMessageRequest,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> StreamingResponse:
    chat_store = request.app.state.chat_store
    registry = request.app.state.registry

    limiter.hit(
        f"msg:{user['id']}",
        settings.message_rate_limit,
        settings.message_window_seconds,
    )

    if await chat_store.get(chat_id, user["id"]) is None:
        raise ApiError("NOT_FOUND", "Чат не найден", status=404)
    plugin = _check_plugin(registry, payload.plugin_id)
    manifest = plugin.get_manifest()

    async def event_stream() -> AsyncGenerator[bytes, None]:
        lock = registry.get_chat_lock(chat_id)
        collected: list[str] = []
        user_msg_id = 0
        disconnected = False

        try:
            async with lock:
                history = await _build_history(
                    chat_store, chat_id, manifest.max_history_chars,
                )
                user_msg_id = await chat_store.add_message(
                    chat_id, "user", payload.content,
                )
                sem = registry.get_semaphore(payload.plugin_id)
                async with sem:
                    async def _consume() -> AsyncGenerator[str, None]:
                        async for delta in plugin.execute_stream(
                            payload.content, history,
                        ):
                            if await request.is_disconnected():
                                raise asyncio.CancelledError()
                            collected.append(delta)
                            yield delta

                    async for delta in _consume():
                        chunk = json.dumps(
                            {"delta": delta}, ensure_ascii=False,
                        )
                        yield f"data: {chunk}\n\n".encode("utf-8")

                assistant_id = await chat_store.add_message(
                    chat_id, "assistant", "".join(collected),
                )
                done = json.dumps(
                    {"done": True, "assistant_message_id": assistant_id},
                    ensure_ascii=False,
                )
                yield f"data: {done}\n\n".encode("utf-8")

        except asyncio.CancelledError:
            disconnected = True
            if user_msg_id and collected:
                try:
                    await chat_store.add_message(
                        chat_id, "assistant", "".join(collected),
                    )
                except Exception:
                    pass
            raise
        except Exception as exc:
            if user_msg_id and collected:
                try:
                    await chat_store.add_message(
                        chat_id, "assistant", "".join(collected),
                    )
                except Exception:
                    pass
            error = json.dumps(
                {"error": str(exc)}, ensure_ascii=False,
            )
            yield f"data: {error}\n\n".encode("utf-8")
        finally:
            if not disconnected:
                yield b"data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )