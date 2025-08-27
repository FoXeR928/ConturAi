from ollama import chat
from loguru import logger

from db_modules.db_query_chat import create_message
from db_modules.db_query_config import get_config_ai
from ai_chat.query_rag_db import search_docs


def ask_query(query:str, chat_id:int, messages_history:list[dict[str, str]]):
    context = search_docs(query)
    ai_model = get_config_ai(name="model")
    prompt = str(get_config_ai(name="pront")).format(context=context, quest=query)
    messages_history.append({"role": "user", "content": prompt})
    try:
        response = chat(model=ai_model, messages=messages_history, stream=False)
        logger.debug("Создан ответ нейросети на вопрос")
        result= create_message("system", chat_id, response["message"]["content"])
    except Exception as err:
        logger.error(f"Не удалось создать ответ нейросети Ошибка {err}")
        result= {
                "result": False,
                "message": "Ошибка сервера сообщение не создано",
                "category": "error",
                "cod": 500,
            }
    return result