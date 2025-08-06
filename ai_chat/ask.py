from ollama import chat
from loguru import logger

from db.db_query_chat import create_message
from db.db_query_config import get_config_ai
from ai_chat.query_rag_db import search_docs


def ask_query(query, chat_id, messages_history):
    context = search_docs(query)
    ai_name = get_config_ai(name="ai_name")
    ai_model = get_config_ai(name="model")
    system_promt=str(get_config_ai(name='system_promt')).format(name=ai_name)
    prompt = str(get_config_ai(name='pront')).format(context=context,quest=query)
    messages_history.append({"role": "user", "content": prompt})
    try:
        response = chat(model=ai_model,system=system_promt, messages=messages_history,stream=False)
        result = response["message"]["content"]
        logger.debug("Создан ответ нейросети на вопрос")
    except Exception as err:
        logger.error(f"Не удалось создать ответ нейросети Ошибка {err}")
        return None
    create_message("system", chat_id, response["message"]["content"])
    return result
