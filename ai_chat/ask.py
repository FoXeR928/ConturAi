from ollama import chat
from loguru import logger

from db.db_query_chat import create_message
from db.db_query_config import get_config
from ai_chat.query_rag_db import search_docs
from instance.config import AI_MODEL


def ask_query(query, chat_id, messages_history):
    context = search_docs(query)
    ai_name=get_config(name='ai_name')
    ai_login=get_config(name='ai_login')
    prompt = f"""Тебя зовут {ai_name}, твоя задача искать информацию в базе и отвечать на вопросы на основе информации из базы.

Информация из базы: {context}

Вопрос или сообщение от пользователя: {query}

Ответ сформирован в формате блока HTML:
Не создавать и не добавлять заголовок
Равернутый ответ на русском, используя информацию из базы выше или сгенеринуй самостоятельно, в формате: <p>Текст ответа</p>
Добавлять таблицу только если нужно в формате: <table>Таблица со значениями<table>
Если ответа на вопрос сгенерирован без информации из базы добавь в ответ: <span>Информация сгенерирована нейросетью, без использования информации из базы знаний.</span>
"""
    messages_history.append({"role": "user", "content": prompt})
    try:
        response = chat(model=AI_MODEL, messages=messages_history)
        result = response["message"]["content"]
        logger.debug("Создан ответ нейросети на вопрос")
    except Exception as err:
        logger.error(f"Не удалось создать ответ нейросети Ошибка {err}")
        return None
    create_message(ai_login, chat_id, response["message"]["content"])
    return result
