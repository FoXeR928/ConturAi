from sqlalchemy import select,update
from loguru import logger

from db.db_create import Users, Chats, Messages, db


def create_chat(login, chat):
    session = db.session
    try:
        create_chat_query = Chats(user_login=login, chat_name=chat)
        session.add(create_chat_query)
        session.commit()
        logger.success(f"Создан чат пользователем {login}")
    except Exception as err:
        logger.error(f"Не удалось создать чат пользователя {login} Ошибка {err}")
    session.close()


def get_chats(login):
    session = db.session
    try:
        user_chats = session.execute(
            select(Users.login).where(Users.login == login)
        ).one_or_none()
        logger.trace(f"Проверка существования пользователя {login} прошла успешно")
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование пользователя {login} Ошибка {err}"
        )
    if not (user_chats == None):
        try:
            result = dict()
            chats = session.execute(
                select(Chats.id, Chats.chat_name).where((Chats.user_login == login) & (Chats.chat_del!=True))
            ).all()
            for chat in chats:
                result[chat[0]] = chat[1]
            logger.debug(f"Получение чатов пользователя {login} прошло успешно")
        except Exception as err:
            logger.warning(
                f"Не удалось получить чаты пользователя {login} Ошибка {err}"
            )
    else:
        result = {None: None}
    session.close()
    return result


def create_message(login, chat_id, text):
    session = db.session
    try:
        user = session.execute(
            select(Users.login).where(Users.login == login)
        ).one_or_none()
        chat = session.execute(
            select(Chats.id).where(Chats.id == chat_id)
        ).one_or_none()
        logger.trace(
            f"Проверка существования пользователя {login} и чата {chat_id} прошла успешно"
        )
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование пользователя {login} и чата {chat_id} Ошибка {err}"
        )
    if user.login == login and chat != None:
        try:
            add_message_query = Messages(user_login=login, chat_id=chat_id, text=text)
            session.add(add_message_query)
            session.commit()
            logger.trace(f"Сообщение в чате {chat_id} создано")
        except Exception as err:
            logger.error(f"Не удалось записать сообщение в чат {chat_id} Ошибка {err}")
    session.close()

def del_messages(chat_id):
    session = db.session
    try:
        chat = session.execute(
            select(Chats.id).where(Chats.id == chat_id)
        ).one_or_none()
        logger.trace(
            f"Проверка существования чата {chat_id} прошла успешно"
        )
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование чата {chat_id} Ошибка {err}"
        )
    if chat!=None:
        try:
            session.execute(update(Chats).where(Chats.id==chat_id).values(chat_del=True))
            session.commit()
            logger.warning(f'Чат {chat_id} помечен как удаленный')
        except Exception as err:
            logger.error(f"Не удалось измеить статус чата {chat_id} Ошибка {err}")
    session.close()

def get_messages_ai(chat_id):
    session = db.session
    try:
        chat = session.execute(
            select(Chats.id).where(Chats.id == chat_id)
        ).one_or_none()
        logger.trace(f"Проверка существования чата {chat_id} прошла успешно")
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование чата {chat_id} Ошибка {err}"
        )
    if chat != None:
        result = list()
        try:
            messages_query = session.execute(
                select(
                    Users.chat_role,
                    Messages.text,
                )
                .select_from(Messages)
                .join(Users, Messages.user_login == Users.login)
                .where(Messages.chat_id == chat_id)
            ).all()
            for i in messages_query:
                result.append({"role": i[0], "content": i[1]})
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


def get_messages_chat(login, chat_id):
    session = db.session
    try:
        user = session.execute(
            select(Users.login).where(Users.login == login)
        ).one_or_none()
        chat = session.execute(
            select(Chats.id).where(Chats.id == chat_id)
        ).one_or_none()
        logger.trace(
            f"Проверка существования пользователя {login} и чата {chat_id} прошла успешно"
        )
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование пользователя {login} и чата {chat_id} Ошибка {err}"
        )
    if user.login == login and chat != None:
        try:
            messages_query = session.execute(
                select(
                    Messages.user_login,
                    Messages.id,
                    Messages.text,
                ).where(Messages.chat_id == chat_id)
            ).all()
            get_name = session.execute(
                select(Chats.chat_name).where(Chats.id == chat_id)
            ).one()
            result = {"name": get_name.chat_name, "messages": messages_query}
            logger.debug(f"Получена историю чата {chat_id} для пользователя {login}")
        except Exception as err:
            logger.error(
                f"Не удалось получить историю чата {chat_id} для пользователя {login} Ошибка {err}"
            )
    else:
        result = {
            "name": "Нет такого чата",
            "messages": [("system", 0, "Чата нет в базе")],
        }
    session.close()
    return result
