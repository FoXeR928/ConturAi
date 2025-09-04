from sqlalchemy import select
from loguru import logger

from db_modules.db_create import Users, session_create, Chats, Configs
from db_modules.db_query_config import get_config_ai


def check_user(login: str):
    session = session_create
    try:
        user = session.scalars(select(Users).where(Users.login == login)).one_or_none()
        logger.trace(f"Проверка пользователя {login} в базе")
        if user != None:
            result = True
        else:
            result = False
        logger.debug(f"Проверка пользователя {login} в базе прошла успешно")
    except Exception as err:
        logger.error(f"Не удалось проверить пользователя {login} Ошибка {err}")
        result = False
    finally:
        session.close()
    return result


def check_chat(chat_id: int):
    session = session_create
    try:
        chat = session.scalars(select(Chats).where(Chats.id == chat_id)).one_or_none()
        logger.trace(f"Проверка чата {chat_id} в базе")
        if chat != None:
            result = True
        else:
            result = False
        logger.debug(f"Проверка чата {chat_id} в базе прошла успешно")
    except Exception as err:
        logger.error(f"Не удалось проверить чата {chat_id} Ошибка {err}")
        result = False
    finally:
        session.close()
    return result


def check_chat_right(login: str, chat_id: int):
    session = session_create
    try:
        chat_user = session.scalars(
            select(Chats.user_login).where(Chats.id == chat_id)
        ).one_or_none()
        logger.trace(f"Проверка чата {chat_id} в базе")
        if chat_user == login:
            result = True
        else:
            result = False
        logger.debug(f"Проверка прав на чат {chat_id} в базе прошла успешно")
    except Exception as err:
        logger.error(f"Не удалось проверить прав на чат {chat_id} Ошибка {err}")
        result = False
    finally:
        session.close()
    return result


def check_config_ai():
    config_list = (
        "model_chunk",
        "model",
        "collection",
        "rag_host",
        "rag_port_http",
        "rag_port_grpc",
        "rag_grpc",
    )
    result_list = list()
    for config in config_list:
        if get_config_ai(name=config) == None:
            result_list.append(False)
        else:
            result_list.append(True)
    return all(result_list)
