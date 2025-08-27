from sqlalchemy import select
from loguru import logger

from db_modules.db_create import session_create, Users, Messages
from db_modules.db_query_config import get_config_ai
from db_modules.db_query import check_user, check_chat
from ai_chat.ask import ask_query


def create_message_ai_query(login: str, chat_id: int, text: str):
    user = check_user(login=login)
    chat = check_chat(chat_id=chat_id)
    if user == True and chat == True:
        session = session_create()
        try:
            add_message_query = Messages(user_login=login, chat_id=chat_id, text=text)
            session.add(add_message_query)
            session.commit()
            logger.trace(f"Сообщение в чате {chat_id} создано")
            result = {
                "result": True,
                "message": "Сообщение создано",
                "category": "success",
                "cod": 201,
            }
            messages_history = get_messages_ai_query(chat_id=chat_id)
            result = ask_query(
                query=text, chat_id=chat, messages_history=messages_history
            )
        except Exception as err:
            logger.error(f"Не удалось записать сообщение в чат {chat_id} Ошибка {err}")
            result = {
                "result": False,
                "message": "Ошибка сервера сообщение не создано",
                "category": "error",
                "cod": 500,
            }
        finally:
            session.close()
    else:
        result = {
            "result": False,
            "message": "Не найден чат",
            "category": "warning",
            "cod": 404,
        }
    return result


def get_messages_ai_query(chat_id: int):
    chat = check_chat(chat_id=chat_id)
    if chat == True:
        session = session_create()
        try:
            ai_name = get_config_ai(name="ai_name")
            system_promt = str(get_config_ai(name="system_promt")).format(name=ai_name)
            result = [{"role": "system", "content": system_promt}]
            messages_query = session.execute(
                select(
                    Users.chat_role,
                    Messages.text,
                )
                .select_from(Messages)
                .join(Users, Messages.user_login == Users.login)
                .where(Messages.chat_id == chat_id)
            ).all()
            for message in messages_query:
                result.append({"role": message[0], "content": message[1]})
            logger.trace(
                f"Получение истории чата {chat_id} и создание истории для AI прошла успешно"
            )
        except Exception as err:
            logger.error(
                f"Не удалось получение истории чата {chat_id} и создать истории для AI Ошибка {err}"
            )
            result = None
    else:
        result = None
    session.close()
    return result
