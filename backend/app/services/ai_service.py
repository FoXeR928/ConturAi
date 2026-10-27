
import os
os.environ["TIKTOKEN_CACHE_DIR"] = "/app/.tiktoken_cache"

import json
import httpx
from uuid import UUID
from loguru import logger
from openai import AsyncOpenAI
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from fastapi.responses import StreamingResponse

from app.core.config import SYSTEM_LOGIN
from app.core.exceptions import AppError
from app.db.models import Chat, Message, User, FewShot
from app.rag import format_context, search_documents
from app.services import llm_config_service, prompt_service

_client: AsyncOpenAI | None = None
_client_key: tuple[str, str] | None = None

# Глобальный энкодер для подсчета токенов (cl100k_base хорошо работает с англ. и рус. для Qwen/Llama)
_encoder = tiktoken.get_encoding("cl100k_base")

def _count_tokens(text: str) -> int:
    return len(_encoder.encode(text))

def _trim_to_tokens(text: str, max_tokens: int) -> str:
    """Обрезает текст до заданного количества токенов."""
    tokens = _encoder.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return _encoder.decode(tokens[:max_tokens]) + "..."

def _get_client(base_url: str, api_key: str) -> AsyncOpenAI:
    global _client, _client_key
    key = (base_url, api_key)
    if _client is None or _client_key != key:
        _client = AsyncOpenAI(base_url=base_url, api_key=api_key, timeout=120.0)
        _client_key = key
    return _client


async def _chat_completion(llm: dict, messages: list[dict[str, str]]):
    client = _get_client(llm["base_url"], llm["api_key"])

    kwargs: dict = {
        "model": llm["model"],
        "messages": messages,
        "temperature": llm["temperature"],
        "max_tokens": llm["max_tokens"],
        "top_p": llm["top_p"],
        "presence_penalty": llm["presence_penalty"],
        "frequency_penalty": llm["frequency_penalty"],
        "stream": llm.get("stream", False),
    }
    if llm["seed"] is not None:
        kwargs["seed"] = llm["seed"]
    if llm["top_k"] and llm["top_k"] > 0:
        kwargs["extra_body"] = {"top_k": llm["top_k"]}

    response = await client.chat.completions.create(**kwargs)
    
    # Если стриминг выключен, возвращаем просто строку (как раньше)
    if not llm.get("stream", False):
        return response.choices[0].message.content or ""
        
    # Если стриминг включен, возвращаем асинхронный генератор
    return response


def _safe_format(template: str, **kwargs) -> str:
    try:
        return template.format(**kwargs)
    except KeyError as err:
        logger.warning(f"Плейсхолдер {err} не передан. Шаблон: {template[:100]}...")
        return template
    except Exception as err:
        logger.error(f"Ошибка форматирования промта: {err}")
        return template


async def _build_history(
    session: AsyncSession,
    chat_id: UUID,
    limit: int,
) -> list[dict[str, str]]:
    # Берем последние N сообщений (сортируем по убыванию, чтобы получить самые свежие, затем переворачиваем)
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
    for role, text in reversed(rows): # reversed, чтобы вернуть хронологический порядок
        history.append({"role": role, "content": text})
    return history


async def ask(
    session: AsyncSession,
    user: User,
    chat_id: UUID,
    question: str,
) -> str:
    chat = (
        await session.execute(select(Chat).where(Chat.id == chat_id))
    ).scalar_one_or_none()
    if not chat or chat.is_deleted:
        raise AppError("Не найден чат", "warning", 404)
    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    # 1. Получаем настройки
    llm = await llm_config_service.get_typed(session)
    raw_configs = await llm_config_service.get_all(session)
    
    max_model_len = int(raw_configs.get("vllm_max_model_len", "4096"))
    history_limit = int(raw_configs.get("chat_history_limit", "10"))
    max_answer_tokens = llm["max_tokens"]

    # Бюджет токенов: сколько останется на сам вопрос, RAG и историю
    # Оставляем запас для ответа модели и системного промта
    budget_tokens = max_model_len - max_answer_tokens - 150 
    if budget_tokens < 500:
        # Если max_tokens съедает всё, принудительно уменьшаем ответ
        max_answer_tokens = max(512, int(max_model_len * 0.3))
        budget_tokens = max_model_len - max_answer_tokens - 150

    # 2. RAG (Ограничиваем контекст)
    docs = await search_documents(session, question)
    context = format_context(docs)
    
    # Ограничиваем контекст максимум 40% от бюджета
    max_context_tokens = int(budget_tokens * 0.4)
    context = _trim_to_tokens(context, max_context_tokens)

    # 3. Промты
    prompts = await prompt_service.get_all_prompts(session)
    ai_name = prompts.get("ai_name", "AI")
    system_prompt = prompts.get("system_prompt", "")
    user_prompt = prompts.get("user_prompt", "{quest}")

    system_content = _safe_format(system_prompt, name=ai_name, context=context)
    prompt_text = _safe_format(user_prompt, context=context, quest=question)

    # Считаем токены системного промта
    system_tokens = _count_tokens(system_content)
    prompt_tokens = _count_tokens(prompt_text)
    
    # Сколько осталось на историю
    history_budget = budget_tokens - system_tokens - prompt_tokens
    
    # 4. Собираем историю с учетом лимита
    history = [{"role": "system", "content": system_content}]
    
    if history_budget > 50:
        raw_history = await _build_history(session, chat_id, limit=history_limit)
        
        # Идем с конца (самые свежие), добавляем, пока влезаем в бюджет
        valid_history = []
        current_tokens = 0
        for msg in reversed(raw_history):
            msg_tokens = _count_tokens(msg["content"])
            if current_tokens + msg_tokens > history_budget:
                break
            valid_history.insert(0, msg)
            current_tokens += msg_tokens
            
        history.extend(valid_history)

    history.append({"role": "user", "content": prompt_text})

    # 5. Запрос к LLM
    # Важно: передаем обновленный max_answer_tokens
    llm["max_tokens"] = max_answer_tokens
    
    try:
        answer = await _chat_completion(llm, history)
    except Exception as err:
        logger.error(f"Ошибка при запросе к vLLM: {err}")
        raise AppError("Нейросеть временно недоступна", "error", 503)

    # 6. Сохранить в БД
    time_question = datetime.now(timezone.utc)
    time_answer = time_question + timedelta(milliseconds=10)
    
    session.add(Message(user_login=user.login, chat_id=chat_id, text=question, created_at=time_question))
    session.add(Message(user_login=SYSTEM_LOGIN, chat_id=chat_id, text=answer, created_at=time_answer))
    await session.commit()

    return answer


async def ask_stream(
    session: AsyncSession,
    user: User,
    chat_id: UUID,
    question: str,
    tags: list[str] | None = None,
):
    chat = (await session.execute(select(Chat).where(Chat.id == chat_id))).scalar_one_or_none()
    if not chat or chat.is_deleted:
        raise AppError("Не найден чат", "warning", 404)
    if chat.user_login != user.login and not user.is_admin:
        raise AppError("Нет доступа", "warning", 403)

    docs = await search_documents(session, question, tags=tags)
    context = format_context(docs)

    prompts = await prompt_service.get_all_prompts(session)
    user_prompt = prompts.get("user_prompt", "Вопрос: {quest}")
    prompt = _safe_format(user_prompt, context=context, quest=question)

    history = await _build_history(session, chat_id, context=context)
    history.append({"role": "user", "content": prompt})

    llm = await llm_config_service.get_typed(session)
    
    # Проверка доступности vLLM
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{llm['base_url'].rsplit('/v1', 1)[0]}/health")
            if resp.status_code != 200:
                raise Exception("Health check failed")
    except Exception:
        logger.warning("vLLM недоступен (Health Check failed)")
        raise AppError("Нейросеть перезагружается или недоступна. Подождите 1-2 минуты.", "warning", 503)

    client = _get_client(llm["base_url"], llm["api_key"])
    
    kwargs = {
        "model": llm["model"],
        "messages": history,
        "temperature": llm["temperature"],
        "max_tokens": llm["max_tokens"],
        "top_p": llm["top_p"],
        "stream": True,  
    }
    if llm["seed"] is not None: kwargs["seed"] = llm["seed"]
    if llm["top_k"] and llm["top_k"] > 0: kwargs["extra_body"] = {"top_k": llm["top_k"]}

    async def stream_generator():
        full_answer = ""
        try:
            response = await client.chat.completions.create(**kwargs)
            async for chunk in response:
                content = chunk.choices[0].delta.content or ""
                if content:
                    full_answer += content
                    yield f"data: {json.dumps({'text': content}, ensure_ascii=False)}\n\n" # <-- ТЕПЕРЬ ИМПОРТ ЕСТЬ
        except Exception as err:
            logger.error(f"Ошибка стриминга: {err}")
            yield f"data: {json.dumps({'error': 'Ошибка генерации'}, ensure_ascii=False)}\n\n"
            return

        time_question = datetime.now(timezone.utc)
        time_answer = time_question + timedelta(milliseconds=10)
        session.add(Message(user_login=user.login, chat_id=chat_id, text=question, created_at=time_question))
        session.add(Message(user_login=SYSTEM_LOGIN, chat_id=chat_id, text=full_answer, created_at=time_answer))
        await session.commit()
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")