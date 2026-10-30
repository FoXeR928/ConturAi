from __future__ import annotations

import asyncio
import json
import time
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
)
from app.schemas.plugin import (
    ChatMessage,
    PipelineContext,
    PipelineTraceItem,
)


router = APIRouter(prefix="/api/v1/chats", tags=["chats"])


async def _run_pipeline(
    plugins: list[Any],
    ctx: PipelineContext,
) -> tuple[PipelineContext, list[PipelineTraceItem]]:
    trace: list[PipelineTraceItem] = []
    for plugin in plugins:
        manifest = plugin.get_manifest()
        started = time.monotonic()
        try:
            ctx = await asyncio.wait_for(
                plugin.execute(ctx),
                timeout=float(manifest.execution_timeout),
            )
            duration = int((time.monotonic() - started) * 1000)
            trace.append(
                PipelineTraceItem(
                    plugin_id=manifest.id,
                    plugin_name=manifest.name,
                    duration_ms=duration,
                    ok=True,
                )
            )
        except asyncio.TimeoutError:
            raise ApiError(
                "PLUGIN_TIMEOUT",
                f"Плагин {manifest.id} не ответил за {manifest.execution_timeout}s",
                status=504,
            ) from None
        except Exception as exc:
            raise ApiError(
                "PLUGIN_ERROR",
                f"Плагин {manifest.id}: {exc}",
                status=502,
            ) from exc
    return ctx, trace


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


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: str,
    payload: SendMessageRequest,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    chat_store = request.app.state.chat_store
    registry = request.app.state.registry

    limiter.hit(
        f"msg:{user['id']}",
        settings.message_rate_limit,
        settings.message_window_seconds,
    )

    if await chat_store.get(chat_id, user["id"]) is None:
        raise ApiError("NOT_FOUND", "Чат не найден", status=404)

    plugins = registry.active_pipeline()
    if not plugins:
        raise ApiError(
            "NO_PLUGINS",
            "Нет активных плагинов — некому обработать сообщение",
            status=503,
        )

    lock = registry.get_chat_lock(chat_id)
    async with lock:
        user_msg_id = await chat_store.add_message(
            chat_id, "user", payload.content,
        )

        ctx = PipelineContext(
            prompt=payload.content,
            metadata={"chat_id": chat_id, "user_id": user["id"]},
        )
        ctx, trace = await _run_pipeline(plugins, ctx)

        if not ctx.answer:
            raise ApiError(
                "NO_ANSWER",
                "Ни один плагин не сформировал ответ (проверьте, включён ли LLM-плагин)",
                status=502,
            )

        assistant_msg_id = await chat_store.add_message(
            chat_id, "assistant", ctx.answer,
        )

    return {
        "user_message": {
            "id": user_msg_id,
            "role": "user",
            "content": payload.content,
            "created_at": "",
        },
        "assistant_message": {
            "id": assistant_msg_id,
            "role": "assistant",
            "content": ctx.answer,
            "created_at": "",
        },
        "trace": [t.model_dump() for t in trace],
    }


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

    plugins = registry.active_pipeline()
    if not plugins:
        raise ApiError("NO_PLUGINS", "Нет активных плагинов", status=503)

    async def event_stream() -> AsyncGenerator[bytes, None]:
        lock = registry.get_chat_lock(chat_id)
        collected: list[str] = []
        disconnected = False
        trace: list[PipelineTraceItem] = []
        user_msg_id = 0

        try:
            async with lock:
                user_msg_id = await chat_store.add_message(
                    chat_id, "user", payload.content,
                )
                ctx = PipelineContext(
                    prompt=payload.content,
                    metadata={"chat_id": chat_id, "user_id": user["id"]},
                )

                for plugin in plugins:
                    manifest = plugin.get_manifest()
                    started = time.monotonic()

                    if manifest.provides_stream:
                        async def _consume(pl=plugin):
                            async for chunk in pl.execute_stream(ctx):
                                if await request.is_disconnected():
                                    raise asyncio.CancelledError()
                                collected.append(chunk)
                                line = json.dumps(
                                    {"delta": chunk}, ensure_ascii=False,
                                )
                                yield f"data: {line}\n\n".encode("utf-8")

                        async for chunk_bytes in _consume():
                            yield chunk_bytes
                        duration = int((time.monotonic() - started) * 1000)
                        trace.append(
                            PipelineTraceItem(
                                plugin_id=manifest.id,
                                plugin_name=manifest.name,
                                duration_ms=duration,
                                ok=True,
                            )
                        )
                    else:
                        try:
                            ctx = await asyncio.wait_for(
                                plugin.execute(ctx),
                                timeout=float(manifest.execution_timeout),
                            )
                            duration = int((time.monotonic() - started) * 1000)
                            trace.append(
                                PipelineTraceItem(
                                    plugin_id=manifest.id,
                                    plugin_name=manifest.name,
                                    duration_ms=duration,
                                    ok=True,
                                )
                            )
                        except Exception as exc:
                            duration = int((time.monotonic() - started) * 1000)
                            trace.append(
                                PipelineTraceItem(
                                    plugin_id=manifest.id,
                                    plugin_name=manifest.name,
                                    duration_ms=duration,
                                    ok=False,
                                    error=str(exc),
                                )
                            )
                            raise

                if not ctx.answer and collected:
                    ctx.answer = "".join(collected)

                if not ctx.answer:
                    raise RuntimeError("Пайплайн не сформировал ответ")

                assistant_id = await chat_store.add_message(
                    chat_id, "assistant", ctx.answer,
                )
                done = json.dumps(
                    {
                        "done": True,
                        "assistant_message_id": assistant_id,
                        "trace": [t.model_dump() for t in trace],
                    },
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
            error = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"data: {error}\n\n".encode("utf-8")
        finally:
            if not disconnected:
                yield b"data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )