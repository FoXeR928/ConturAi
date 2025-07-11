from ollama import chat
from loguru import logger

from db.db_query_chat import create_message, get_messages_ai
from ai_chat.query_rag_db import search_docs
from config.config import AI_MODEL, AI_LOGIN, AI_NAME


def ask_query(query, chat_id, messages_history):
    context = search_docs(query)
    prompt = f"""Тебя зовут {AI_NAME}, твоя задача искать информацию в базе и отвечать на вопросы на основе информации из базы.

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
        result=response["message"]["content"]
        logger.debug('Создан ответ нейросети на вопрос')
    except Exception as err:
        logger.error(f'Не удалось создать ответ нейросети Ошибка {err}')
        return None
    create_message(AI_LOGIN, chat_id, response["message"]["content"])
    return result
