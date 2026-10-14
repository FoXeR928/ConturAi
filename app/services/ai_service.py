from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import SYSTEM_LOGIN
from app.core.exceptions import AppError
from app.db.models import Chat, Message, User
from app.llm.vllm_client import chat_completion
from app.rag.store import format_context, search_documents


async def _build_history(
    session: AsyncSession, chat_id: int
) -> list[dict[str, str]]:
    history: list[dict[str, str]] = [
        {
            "role": "system",
            "content": settings.system_prompt.format(name=settings.ai_name),
        }
    ]
    rows = (
        await session.execute(
            select(User.chat_role, Message.text)
            .join(User, User.login == Message.user_login)
            .where(Message.chat_id == chat_id)
            .order_by(Message.id)
        )
    ).all()
    for role, text in rows:
        history.append({"role": role, "content": text})
    return history


async def ask(
    session: AsyncSession, user: User, chat_id: int, question: str
) -> str:
    chat = (
        await session.execute(select(Chat).where(Chat.id == chat_id))
    ).scalar_one_or_none()
    if not chat:
        raise AppError("Не найден чат", "warning", 404)
    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    # 1. сохраняем сообщение пользователя
    session.add(Message(user_login=user.login, chat_id=chat_id, text=question))
    await session.commit()

    # 2. RAG
    docs = await search_documents(session, question, limit=settings.rag_search_limit)
    context = format_context(docs)

    # 3. промт с контекстом
    prompt = settings.user_prompt.format(context=context, quest=question)

    history = await _build_history(session, chat_id)
    history[-1] = {"role": "user", "content": prompt}

    # 4. запрос к vLLM
    answer = await chat_completion(history)

    # 5. сохраняем ответ
    session.add(
        Message(
            user_login=SYSTEM_LOGIN,
            chat_id=chat_id,
            text=answer,
        )
    )
    await session.commit()
    return answer