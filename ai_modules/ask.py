from ollama import chat
from loguru import logger

from db_modules.db_query_chat import create_message_query
from db_modules.db_query_config import get_config_ai
from ai_modules.query_rag_db import search_docs_rquery


def ask_query(query: str, chat_id: int, messages_history: list[dict[str, str]]):
    context = search_docs_rquery(query=query)
    ai_model = get_config_ai(name="model")
    prompt = str(get_config_ai(name="pront")).format(context=context, quest=query)
    messages_history.append({"role": "user", "content": prompt})
    try:
        response = chat(model=ai_model, messages=messages_history, stream=False)
        logger.debug("Создан ответ нейросети на вопрос")
        return create_message_query(
            login="system",
            chat_id=chat_id,
            text=response["message"]["content"],
            return_text=True,
        )
    except Exception as err:
        logger.error(f"Не удалось создать ответ нейросети Ошибка {err}")
        raise {
            "result": False,
            "message": "Ошибка сервера сообщение не создано",
            "category": "error",
            "cod": 500,
        }
