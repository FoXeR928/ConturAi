from sqlalchemy import select, update, delete
from loguru import logger

from db_modules.db_create import Chats, Messages, session_create
from db_modules.db_query import check_user, check_chat


def create_chat(login: str, chat: str):
    user = check_user(login=login)
    if user == True:
        session = session_create()
        try:
            create_chat_query = Chats(user_login=login, chat_name=chat)
            session.add(create_chat_query)
            session.commit()
            result = {
                "result": True,
                "message": "Чат создан",
                "category": "success",
                "cod": 201,
            }
            logger.debug(f"Создан чат пользователем {login}")
        except Exception as err:
            result = {
                "result": False,
                "message": "Ошибка сервера чат не создан",
                "category": "warning",
                "cod": 500,
            }
            logger.error(f"Не удалось создать чат пользователя {login} Ошибка {err}")
        finally:
            session.close()
    else:
        result = {
            "result": False,
            "message": "Чат не создан из-за отсутсвия пользователя в базе",
            "category": "warning",
            "cod": 404,
        }
    return result


def get_chats(login: str):
    user = check_user(login=login)
    if user == True:
        session = session_create()
        try:
            result_list = dict()
            chats = session.execute(
                select(Chats.id, Chats.chat_name, Chats.date_create).where(
                    (Chats.user_login == login) & (Chats.chat_del != True)
                )
            ).all()
            for chat in chats:
                result_list[chat[0]] = {"chat_name": chat[1], "chat_create": chat[2]}
            result = {
                "result": True,
                "chats": result_list,
                "message": "Чаты получены",
                "category": "success",
                "cod": 200,
            }
            logger.debug(f"Получение чатов пользователя {login} прошло успешно")
        except Exception as err:
            logger.warning(
                f"Не удалось получить чаты пользователя {login} Ошибка {err}"
            )
            result = {
                "result": False,
                "message": "Ошибка сервера чаты не найдены",
                "category": "error",
                "cod": 500,
            }
        finally:
            session.close()
    else:
        result = {
            "result": False,
            "message": "Чаты пользователя в базе не найдены",
            "category": "warning",
            "cod": 404,
        }
    return result


def get_messages_chat(login: str, chat_id: int):
    user = check_user(login=login)
    chat = check_chat(chat_id=chat_id)
    if user == True and chat == True:
        session = session_create()
        try:
            messages_query = session.execute(
                select(
                    Messages.id,
                    Messages.text,
                ).where(Messages.chat_id == chat_id)
            ).all()
            get_name = session.scalars(
                select(Chats.chat_name).where(Chats.id == chat_id)
            ).one()
            result = {
                "result": True,
                "message": "Сообщения получены",
                "chat_name": get_name,
                "messages_history": messages_query,
                "category": "success",
                "cod": 200,
            }
            logger.debug(f"Получена историю чата {chat_id} для пользователя {login}")
        except Exception as err:
            logger.error(
                f"Не удалось получить историю чата {chat_id} для пользователя {login} Ошибка {err}"
            )
            result = {
                "result": False,
                "message": "Ошибка сервера сообщения не найдены",
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


def create_message(login: str, chat_id: int, text: str):
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


def delet_messages(chat_id, user):
    session = db.session
    try:
        chat = session.scalars(
            select(Chats.id).where(Chats.id == chat_id)
        ).one_or_none()
        logger.trace(f"Проверка существования чата {chat_id} прошла успешно")
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование чата {chat_id} Ошибка {err}"
        )
    if chat != None:
        user = session.scalars(
            select(Chats.user_login).where(Chats.id == chat_id)
        ).one_or_none()
        if user == user or get_user_role(user):
            try:
                session.execute(
                    update(Chats).where(Chats.id == chat_id).values(chat_del=True)
                )
                session.commit()
                logger.debug(f"Чат {chat_id} помечен как удаленный")
                flash(message="Чат удален", category="success")
            except Exception as err:
                logger.warning(f"Не удалось измеить статус чата {chat_id} Ошибка {err}")
                flash(message="Чат не удален из-за ошибки", category="error")
        else:
            flash(message="У вас нет права на удаление чата", category="warning")
    else:
        logger.warning(f"Не найден чат {chat_id} Ошибка {err}")
    session.close()


def get_delet_chats_irrevocably():
    session = db.session
    try:
        result = list()
        chats = session.execute(
            select(Chats.id, Chats.chat_name, Chats.user_login).where(
                Chats.chat_del == True
            )
        ).all()
        for chat in chats:
            chat_dict = {"chat_id": chat[0], "chat_name": chat[1], "user": chat[2]}
            result.append(chat_dict)
        logger.trace(f"Чаты для удаления получены из базы")
    except Exception as err:
        logger.error(f"Не удалось получить чаты для удаления из базы Ошибка {err}")
    session.close()
    return result


def delet_chats_irrevocably_checked(chats):
    session = db.session
    for chat in chats:
        try:
            check_del = session.scalar(select(Chats).where(Chats.id == chat))
            logger.trace(f"Проверка чатa {chat} для удаления прошла успешно")
        except Exception as err:
            logger.error(
                f"Не удалось проверить наличие чатa {chat} для удаления Ошибка {err}"
            )
        if check_del != None:
            try:
                session.execute(
                    delete(Chats).where((Chats.chat_del == True) & (Chats.id == chat))
                )
                session.commit()
                logger.debug(f"Чат {chat} удалены из базы")
            except Exception as err:
                logger.error(f"Не удалось удалить чат {chat} Ошибка {err}")
    session.close()


def recovery_chats_checked(chats):
    session = db.session
    for chat in chats:
        try:
            check_del = session.scalar(select(Chats).where(Chats.id == chat))
            logger.trace(f"Проверка чатa {chat} для удаления прошла успешно")
        except Exception as err:
            logger.error(
                f"Не удалось проверить наличие чатa {chat} для удаления Ошибка {err}"
            )
        if check_del != None:
            try:
                session.execute(
                    update(Chats)
                    .where((Chats.chat_del == True) & (Chats.id == chat))
                    .values(chat_del=False)
                )
                session.commit()
                logger.debug(f"Чат {chat} удалены из базы")
            except Exception as err:
                logger.error(f"Не удалось удалить чат {chat} Ошибка {err}")
    session.close()


def delet_chats_irrevocably():
    session = db.session
    try:
        check_del = session.scalar(select(Chats).where(Chats.chat_del == True))
        logger.trace(f"Проверка чатов для удаления прошла успешно")
    except Exception as err:
        logger.error(f"Не удалось проверить наличие чатов для удаления Ошибка {err}")
    if check_del != None:
        try:
            del_chats = session.execute(
                select(Chats.id).where(Chats.chat_del == True)
            ).all()
            for chat in del_chats:
                session.execute(delete(Messages).where(Messages.chat_id == chat[0]))
            session.execute(delete(Chats).where(Chats.chat_del == True))
            session.commit()
            flash(message="Чаты удалены", category="success")
            logger.success(f"Чаты удалены из базы")
        except Exception as err:
            logger.error(f"Не удалось удалить чаты Ошибка {err}")
            flash(message="Чаты не удалены", category="error")
    else:
        flash(
            message="Чаты не удалены, так как чатов на удаление нет",
            category="warning",
        )
    session.close()
