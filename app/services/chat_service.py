from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models import Chat, Message, User


async def _get_chat(session: AsyncSession, chat_id: int) -> Chat:
    chat = (
        await session.execute(select(Chat).where(Chat.id == chat_id))
    ).scalar_one_or_none()
    if not chat:
        raise AppError("Не найден чат", "warning", 404)
    return chat


async def create_chat(session: AsyncSession, user: User, name: str) -> int:
    chat = Chat(user_login=user.login, name=name)
    session.add(chat)
    await session.commit()
    return chat.id


async def list_chats(session: AsyncSession, user: User) -> list[dict]:
    result = await session.execute(
        select(Chat.id, Chat.name, Chat.created_at).where(
            Chat.user_login == user.login, Chat.is_deleted.is_(False)
        )
    )
    return [dict(row._mapping) for row in result.all()]


async def get_messages(
    session: AsyncSession, user: User, chat_id: int
) -> tuple[str, list[dict]]:
    chat = await _get_chat(session, chat_id)
    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    result = await session.execute(
        select(Message.id, Message.text, User.login, User.chat_role)
        .join(User, User.login == Message.user_login)
        .where(Message.chat_id == chat_id)
    )
    messages = [dict(row._mapping) for row in result.all()]
    return chat.name, messages


async def create_message(
    session: AsyncSession, user: User, chat_id: int, text: str
) -> int:
    chat = await _get_chat(session, chat_id)
    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    message = Message(user_login=user.login, chat_id=chat_id, text=text)
    session.add(message)
    await session.commit()
    return message.id


async def soft_delete_chat(session: AsyncSession, user: User, chat_id: int) -> None:
    chat = await _get_chat(session, chat_id)
    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)
    await session.execute(
        update(Chat).where(Chat.id == chat_id).values(is_deleted=True)
    )
    await session.commit()


async def list_deleted_chats(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(Chat.id, Chat.name, Chat.user_login).where(Chat.is_deleted.is_(True))
    )
    return [dict(row._mapping) for row in result.all()]


async def purge_deleted(session: AsyncSession, chat_ids: list[int] | None) -> None:
    stmt = delete(Chat).where(Chat.is_deleted.is_(True))
    if chat_ids:
        stmt = stmt.where(Chat.id.in_(chat_ids))
    await session.execute(stmt)
    await session.commit()


async def restore_chats(session: AsyncSession, chat_ids: list[int]) -> None:
    await session.execute(
        update(Chat).where(Chat.id.in_(chat_ids)).values(is_deleted=False)
    )
    await session.commit()


async def delete_message(
    session: AsyncSession, user: User, chat_id: int, message_id: int
) -> None:
    chat = await _get_chat(session, chat_id)
    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)
    await session.execute(
        delete(Message).where(Message.id == message_id, Message.chat_id == chat_id)
    )
    await session.commit()