from ollama import chat
from loguru import logger

from db.db_query_chat import create_message
from db.db_query_config import get_config
from ai_chat.query_rag_db import search_docs


def ask_query(query, chat_id, messages_history):
    context = search_docs(query)
    ai_name=get_config(name='ai_name')
    ai_model=get_config('ai_model')
    prompt = f"""Тебя зовут {ai_name}, твоя задача искать информацию в базе и отвечать на вопросы на основе информации из базы.

Информация из базы: {context}

Вопрос или сообщение от пользователя: {query}

Равернутый ответ на русском, используя информацию из базы выше или сгенеринуй самостоятельно
Добавлять таблицу только если нужно
Если ответа на вопрос сгенерирован без информации из базы добавь Информация сгенерирована нейросетью, без использования информации из базы знаний.
"""
    messages_history.append({"role": "user", "content": prompt})
    try:
        response = chat(model=ai_model, messages=messages_history)
        result = response["message"]["content"]
        logger.debug("Создан ответ нейросети на вопрос")
    except Exception as err:
        logger.error(f"Не удалось создать ответ нейросети Ошибка {err}")
        return None
    create_message('system', chat_id, response["message"]["content"])
    return result
