from uuid import UUID
from datetime import datetime, timezone, timedelta
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import SYSTEM_LOGIN
from app.core.exceptions import AppError
from app.db.models import Chat, Message, User
from app.kernel import kernel

# ==============================================================================
# БЛОК 1: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================================

async def _build_history(session: AsyncSession, chat_id: UUID, limit: int = 10) -> list[dict[str, str]]:
    """Загружает последние N сообщений чата для контекста."""
    rows = (
        await session.execute(
            select(User.chat_role, Message.text)
            .join(User, User.login == Message.user_login)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
    ).all()
    
    history = []
    for role, text in reversed(rows):
        history.append({"role": role, "content": text})
    return history

# ==============================================================================
# БЛОК 2: ОБЫЧНЫЙ ОТВЕТ
# ==============================================================================

async def ask(
    session: AsyncSession,
    user: User,
    chat_id: UUID,
    question: str,
) -> str:
    # 1. Проверка прав
    chat = (await session.execute(select(Chat).where(Chat.id == chat_id))).scalar_one_or_none()
    if not chat or chat.is_deleted:
        raise AppError("Не найден чат", "warning", 404)
    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    # 2. Получаем LLM-плагин из ядра
    llm_plugin = kernel.registry.get_llm_provider()
    if not llm_plugin:
        raise AppError("Нейросеть не подключена (нет активного LLM-плагина)", "error", 503)

    # 3. Собираем историю
    history = await _build_history(session, chat_id, limit=10)
    history.append({"role": "user", "content": question})

    # 4. Генерируем ответ
    try:
        answer = await llm_plugin.generate(history)
    except Exception as err:
        logger.error(f"Ошибка LLM-плагина: {err}")
        raise AppError("Нейросеть временно недоступна", "error", 503)

    # 5. Сохраняем в БД
    time_question = datetime.now(timezone.utc)
    time_answer = time_question + timedelta(milliseconds=10)
    session.add(Message(user_login=user.login, chat_id=chat_id, text=question, created_at=time_question))
    session.add(Message(user_login=SYSTEM_LOGIN, chat_id=chat_id, text=answer, created_at=time_answer))
    await session.commit()

    return answer


# ==============================================================================
# БЛОК 3: СТРИМИНГОВЫЙ ОТВЕТ
# ==============================================================================

async def ask_stream(
    session: AsyncSession,
    user: User,
    chat_id: UUID,
    question: str,
):
    import json
    from fastapi.responses import StreamingResponse

    # 1. Проверка прав
    chat = (await session.execute(select(Chat).where(Chat.id == chat_id))).scalar_one_or_none()
    if not chat or chat.is_deleted:
        raise AppError("Не найден чат", "warning", 404)
    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    # 2. Получаем LLM-плагин
    llm_plugin = kernel.registry.get_llm_provider()
    if not llm_plugin:
        raise AppError("Нейросеть не подключена", "error", 503)

    # 3. Собираем историю
    history = await _build_history(session, chat_id, limit=10)
    history.append({"role": "user", "content": question})

    # 4. Асинхронный генератор для стриминга
    async def stream_generator():
        full_answer = ""
        try:
            async for chunk in llm_plugin.generate_stream(history):
                full_answer += chunk
                yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
        except Exception as err:
            logger.error(f"Ошибка стриминга LLM-плагина: {err}")
            yield f"data: {json.dumps({'error': 'Ошибка генерации'}, ensure_ascii=False)}\n\n"
            return
        finally:
            # Сохраняем результат в БД после завершения стриминга
            time_question = datetime.now(timezone.utc)
            time_answer = time_question + timedelta(milliseconds=10)
            session.add(Message(user_login=user.login, chat_id=chat_id, text=question, created_at=time_question))
            session.add(Message(user_login=SYSTEM_LOGIN, chat_id=chat_id, text=full_answer, created_at=time_answer))
            await session.commit()
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")