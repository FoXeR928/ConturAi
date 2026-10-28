from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models import Chat, Message, User

# ==============================================================================
# БЛОК 1: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ПОИСК И ПРОВЕРКА ПРАВ)
# ==============================================================================

async def _get_chat(
    session: AsyncSession, chat_id: UUID, include_deleted: bool = False
) -> Chat:
    """
    Внутренняя функция для получения чата по ID с проверкой на удаление.
    Если чат не найден или удален (а мы не просили искать среди удаленных) — выбрасывает 404.
    """
    chat = (
        await session.execute(select(Chat).where(Chat.id == chat_id))
    ).scalar_one_or_none()

    if not chat or (not include_deleted and chat.is_deleted):
        raise AppError("Не найден чат", "warning", 404)
    return chat


# ==============================================================================
# БЛОК 2: УПРАВЛЕНИЕ ЧАТАМИ (СОЗДАНИЕ, СПИСОК, ПЕРЕИМЕНОВАНИЕ)
# ==============================================================================

async def create_chat(session: AsyncSession, user: User, name: str) -> UUID:
    """
    Создает новый чат для конкретного пользователя.
    Возвращает UUID созданного чата, чтобы фронтенд сразу мог переключиться на него.
    """
    chat = Chat(user_login=user.login, name=name)
    session.add(chat)
    await session.commit()
    return chat.id


async def list_chats(session: AsyncSession, user: User) -> list[dict]:
    """
    Возвращает список всех активных (не удаленных) чатов пользователя.
    Сортировка по умолчанию (по дате создания), чтобы новые чаты были сверху.
    """
    result = await session.execute(
        select(Chat.id, Chat.name, Chat.created_at).where(
            Chat.user_login == user.login, Chat.is_deleted.is_(False)
        )
    )
    return [dict(row._mapping) for row in result.all()]


async def rename_chat(session: AsyncSession, user: User, chat_id: UUID, name: str) -> None:
    """
    Изменяет название чата.
    Проверяет, что чат существует и принадлежит этому пользователю (или юзер - админ).
    """
    chat = await _get_chat(session, chat_id, include_deleted=False)
    
    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)
        
    chat.name = name
    await session.commit()


# ==============================================================================
# БЛОК 3: РАБОТА С СООБЩЕНИЯМИ
# ==============================================================================

async def get_messages(
    session: AsyncSession, 
    user: User, 
    chat_id: UUID,
    limit: int | None = None,
    offset: int = 0
) -> tuple[str, list[dict], int]:
    """
    Возвращает название чата, список сообщений и общее количество сообщений.
    
    Если limit задан — возвращает последние N сообщений (пагинация).
    Если limit = None — возвращает всю историю (обратная совместимость).
    """
    chat = await _get_chat(session, chat_id, include_deleted=user.is_admin)

    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    # Считаем общее количество сообщений в чате (для фронтенда)
    count_stmt = select(Message).where(Message.chat_id == chat_id)
    total_count = len((await session.execute(count_stmt)).scalars().all())

    # Формируем базовый запрос
    stmt = (
        select(Message.id, Message.text, User.login, User.chat_role, Message.created_at)
        .join(User, User.login == Message.user_login)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
    )

    if limit:
        # Если запрошена пагинация: берем последние сообщения (сортируем по убыванию и отступаем)
        stmt = stmt.offset(offset).limit(limit)
        rows = (await session.execute(stmt)).all()
        # Переворачиваем в хронологический порядок
        messages = [dict(r._mapping) for r in reversed(rows)]
    else:
        # Если limit=None — берем всё
        rows = (await session.execute(stmt)).all()
        messages = [dict(r._mapping) for r in reversed(rows)]

    return chat.name, messages, total_count


async def create_message(
    session: AsyncSession, user: User, chat_id: UUID, text: str
) -> UUID:
    """
    Создание обычного текстового сообщения (без вызова LLM).
    Проверяет права доступа к чату.
    """
    chat = await _get_chat(session, chat_id, include_deleted=False)

    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    message = Message(user_login=user.login, chat_id=chat_id, text=text)
    session.add(message)
    await session.commit()
    return message.id


async def delete_message(
    session: AsyncSession, user: User, chat_id: UUID, message_id: UUID
) -> None:
    """
    Удаляет конкретное сообщение из чата.
    Проверяет, что сообщение относится к указанному чату (для безопасности).
    """
    chat = await _get_chat(session, chat_id, include_deleted=False)

    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    await session.execute(
        delete(Message).where(Message.id == message_id, Message.chat_id == chat_id)
    )
    await session.commit()


# ==============================================================================
# БЛОК 4: КОРЗИНА (МЯГКОЕ УДАЛЕНИЕ И ВОССТАНОВЛЕНИЕ)
# ==============================================================================

async def soft_delete_chat(session: AsyncSession, user: User, chat_id: UUID) -> None:
    """
    Мягкое удаление чата (перемещение в корзину).
    Вместо физического удаления ставит флаг is_deleted = True.
    Сообщения и сам чат остаются в БД.
    """
    chat = await _get_chat(session, chat_id, include_deleted=False)

    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    await session.execute(
        update(Chat).where(Chat.id == chat_id).values(is_deleted=True)
    )
    await session.commit()


async def list_deleted_chats(session: AsyncSession) -> list[dict]:
    """
    Возвращает список всех удаленных чатов (для корзины админа).
    """
    result = await session.execute(
        select(Chat.id, Chat.name, Chat.user_login).where(Chat.is_deleted.is_(True))
    )
    return [dict(row._mapping) for row in result.all()]


async def restore_chats(session: AsyncSession, chat_ids: list[UUID]) -> None:
    """
    Восстановление чатов из корзины.
    Снимает флаг is_deleted.
    """
    await session.execute(
        update(Chat).where(Chat.id.in_(chat_ids)).values(is_deleted=False)
    )
    await session.commit()


# ==============================================================================
# БЛОК 5: БЕЗВОЗВРАТНОЕ УДАЛЕНИЕ
# ==============================================================================

async def purge_deleted(
    session: AsyncSession, chat_ids: list[UUID] | None
) -> None:
    """
    Безвозвратное удаление чатов из базы данных.
    
    Если передан список chat_ids — удаляет только их (при условии, что они в корзине).
    Если chat_ids = None — полностью очищает корзину.
    При физическом удалении чата, все его сообщения удалятся автоматически (ON DELETE CASCADE).
    """
    stmt = delete(Chat).where(Chat.is_deleted.is_(True))
    if chat_ids:
        stmt = stmt.where(Chat.id.in_(chat_ids))
    await session.execute(stmt)
    await session.commit()