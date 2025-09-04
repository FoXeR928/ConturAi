from sqlalchemy import select, update, delete
from loguru import logger

from db_modules.db_create import Chats, Messages, Users, session_create
from db_modules.db_query import check_user, check_chat, check_chat_right
from api.api_auth import User


def create_chat_query(login: str, chat: str):
    if check_user(login=login) == True:
        session = session_create
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


def get_chats_query(login: str):
    if check_user(login=login) == True:
        session = session_create
        try:
            chats = session.execute(
                select(Chats.id, Chats.chat_name, Chats.date_create).where(
                    (Chats.user_login == login) & (Chats.chat_del == False)
                )
            ).all()
            chats = [row._mapping for row in chats]
            result = {
                "result": True,
                "message": "Чаты получены",
                "chats": chats,
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


def get_messages_chat_query(login: str, chat_id: int):
    if check_user(login=login) == True and check_chat(chat_id=chat_id) == True:
        session = session_create
        try:
            messages_query = session.execute(
                select(
                    Messages.id,
                    Messages.text,
                    Users.login,
                    Users.chat_role,
                )
                .where(Messages.chat_id == chat_id)
                .join(Users)
            ).all()
            get_name = session.scalars(
                select(Chats.chat_name).where(Chats.id == chat_id)
            ).one()
            messages = [row._mapping for row in messages_query]
            result = {
                "result": True,
                "message": "Сообщения получены",
                "chat_name": get_name,
                "messages_history": messages,
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


def create_message_query(
    login: str, chat_id: int, text: str, return_text: bool = False
):
    if check_user(login=login) == True and check_chat(chat_id=chat_id) == True:
        session = session_create
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
            if return_text == True:
                result["answer"] = text
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


def delet_chat_query(user: User, chat_id: int):
    if check_chat(chat_id=chat_id) == True:
        if (
            check_chat_right(login=user.login, chat_id=chat_id) == True
            or user.isAdmin == True
        ):
            session = session_create
            try:
                session.execute(
                    update(Chats).where(Chats.id == chat_id).values(chat_del=True)
                )
                session.commit()
                logger.debug(
                    f"Чат {chat_id} помечен на удаленние пользователем {user.login}"
                )
                result = {
                    "result": True,
                    "message": "Чат удален",
                    "category": "success",
                    "cod": 201,
                }
            except Exception as err:
                logger.error(f"Не удалось удалить чат {chat_id} Ошибка {err}")
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
                "message": "Нет доступа",
                "category": "warning",
                "cod": 403,
            }
    else:
        result = {
            "result": False,
            "message": "Не найден чат",
            "category": "warning",
            "cod": 404,
        }
    return result


def get_delet_chats_query():
    session = session_create
    try:
        result = list()
        chats_get = session.execute(
            select(Chats.id, Chats.chat_name, Chats.user_login).where(
                Chats.chat_del == True
            )
        ).all()
        chats = [row._mapping for row in chats_get]
        result = {
            "result": True,
            "message": "Чаты на удаление получены",
            "chats": chats,
            "category": "success",
            "cod": 200,
        }
        logger.trace(f"Чаты для удаления получены из базы")
    except Exception as err:
        logger.error(f"Не удалось получить чаты для удаления из базы Ошибка {err}")
        result = {
            "result": False,
            "message": "Ошибка сервера не удалось получить чаты на удаление",
            "category": "error",
            "cod": 500,
        }
    finally:
        session.close()
    return result


def delet_chats_irrevocably_list_query(chats: list):
    chats_delet = list()
    for chat in chats:
        if check_chat(chat_id=chat) == True:
            session = session_create
            try:
                session.execute(
                    delete(Chats).where((Chats.chat_del == True) & (Chats.id == chat))
                )
                session.commit()
                chats_delet.append({chat: "success"})
                logger.debug(f"Чат {chat} удалены из базы")
            except Exception as err:
                logger.error(f"Не удалось удалить чат {chat} Ошибка {err}")
                chats_delet.append({chat: "error"})
            finally:
                session.close()
        else:
            chats_delet.append({chat: "not found"})
    return {
        "result": True,
        "message": "Чаты удалены безвозвратно",
        "chats_result": chats_delet,
        "category": "success",
        "cod": 201,
    }


def delet_chats_irrevocably_all_list():
    session = session_create
    try:
        session.execute(delete(Chats).where(Chats.chat_del == True))
        session.commit()
        result = {
            "result": True,
            "message": "Чаты удалены",
            "category": "success",
            "cod": 201,
        }
        logger.success(f"Чаты удалены из базы")
    except Exception as err:
        result = {
            "result": False,
            "message": "Ошибка сервера не удалось удалить чаты",
            "category": "error",
            "cod": 500,
        }
        logger.error(f"Не удалось удалить чаты Ошибка {err}")
    finally:
        session.close()
    return result


def recovery_chats_list_query(chats: list):
    chats_delet = list()
    for chat in chats:
        if check_chat(chat_id=chat) == True:
            session = session_create
            try:
                session.execute(
                    update(Chats)
                    .where((Chats.chat_del == True) & (Chats.id == chat))
                    .values(chat_del=False)
                )
                session.commit()
                chats_delet.append({chat: "success"})
                logger.debug(f"Чат {chat} восствновлен")
            except Exception as err:
                logger.error(f"Не удалось восстановить чат {chat} Ошибка {err}")
                chats_delet.append({chat: "error"})
            finally:
                session.close()
        else:
            chats_delet.append({chat: "not found"})
    return {
        "result": True,
        "message": "Чаты восстановлены",
        "chats_result": chats_delet,
        "category": "success",
        "cod": 201,
    }


def delete_message_query(user: User, chat_id: int, message_id: int):
    if check_chat(chat_id=chat_id) == True:
        if check_chat_right(login=user.login, chat_id=chat_id) == True:
            session = session_create
            try:
                session.execute(
                    delete(Messages).where(
                        (Messages.chat_id == chat_id) & (Messages.id == message_id)
                    )
                )
                session.commit()
                logger.debug(f"Сообщение в чате {chat_id} удаленно")
                result = {
                    "result": True,
                    "message": "Сообщение удалено",
                    "category": "success",
                    "cod": 201,
                }
            except Exception as err:
                logger.warning(
                    f"Не удалось удалить сообщение в чате {chat_id} Ошибка {err}"
                )
                result = {
                    "result": False,
                    "message": "Ошибка сервера сообщение не удалено",
                    "category": "error",
                    "cod": 500,
                }
        else:
            result = {
                "result": False,
                "message": "Нет доступа",
                "category": "warning",
                "cod": 403,
            }
    else:
        result = {
            "result": False,
            "message": "Не найден чат",
            "category": "warning",
            "cod": 404,
        }
    return result
