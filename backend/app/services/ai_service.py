from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import SYSTEM_LOGIN, settings
from app.core.exceptions import AppError
from app.db.models import Chat, Message, User
from app.rag import format_context, search_documents
from app.services import prompt_service

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.vllm_base_url,
            api_key=settings.vllm_api_key,
            timeout=120.0,
        )
    return _client


async def _chat_completion(messages: list[dict[str, str]]) -> str:
    response = await _get_client().chat.completions.create(
        model=settings.vllm_model_name,
        messages=messages,
        temperature=settings.vllm_temperature,
        max_tokens=settings.vllm_max_tokens,
        stream=False,
    )
    return response.choices[0].message.content or ""


async def _build_history(
    session: AsyncSession, chat_id: int
) -> list[dict[str, str]]:
    prompts = await prompt_service.get_all_prompts(session)
    ai_name = prompts.get("ai_name", "AI")
    system_prompt = prompts.get("system_prompt", "")
    history: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt.format(name=ai_name)}
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

    # 1. Ищем контекст
    docs = await search_documents(session, question)
    context = format_context(docs)

    # 2. Готовим промт
    prompts = await prompt_service.get_all_prompts(session)
    user_prompt = prompts.get("user_prompt", "Контекст: {context}\nВопрос: {quest}")
    prompt = user_prompt.format(context=context, quest=question)

    # 3. Собираем историю (без сохранения в БД!)
    history = await _build_history(session, chat_id)
    history.append({"role": "user", "content": prompt})

    # 4. Спрашиваем vLLM
    try:
        answer = await _chat_completion(history)
    except Exception as err:
        from loguru import logger
        logger.error(f"Ошибка при запросе к vLLM: {err}")
        raise AppError("Нейросеть временно недоступна", "error", 503)

    # 5. Сохраняем вопрос и ответ одной транзакцией
    session.add(Message(user_login=user.login, chat_id=chat_id, text=question))
    session.add(Message(user_login=SYSTEM_LOGIN, chat_id=chat_id, text=answer))
    await session.commit()
    
    return answer