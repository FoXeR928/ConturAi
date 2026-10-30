from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session_factory
from ..interfaces.llm_spec import ChatMessage
from ..models import ChatRoom, Message


async def create_room(db: AsyncSession, user_id: uuid.UUID, title: Optional[str]) -> ChatRoom:
    room = ChatRoom(user_id=user_id, title=title or "Новый чат")
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


async def get_room(db: AsyncSession, room_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ChatRoom]:
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.id == room_id, ChatRoom.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_rooms(db: AsyncSession, user_id: uuid.UUID) -> List[ChatRoom]:
    result = await db.execute(
        select(ChatRoom)
        .where(ChatRoom.user_id == user_id)
        .order_by(ChatRoom.updated_at.desc())
    )
    return list(result.scalars().all())


async def list_messages(db: AsyncSession, room_id: uuid.UUID) -> List[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.room_id == room_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def save_user_message(db: AsyncSession, room_id: uuid.UUID, content: str) -> Message:
    msg = Message(room_id=room_id, role="user", content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def save_assistant_message(
    room_id: uuid.UUID, content: str
) -> Optional[uuid.UUID]:
    """Сохраняет ответ ассистента через отдельную сессию — вызывается
    из SSE-генератора после завершения стрима."""
    if not content:
        return None
    async with async_session_factory() as session:
        msg = Message(room_id=room_id, role="assistant", content=content)
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg.id


def messages_to_chat(rows: List[Message]) -> List[ChatMessage]:
    return [ChatMessage(role=m.role, content=m.content) for m in rows]