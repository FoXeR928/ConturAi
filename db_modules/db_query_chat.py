from sqlalchemy import select, update, delete
from loguru import logger

from db_modules.db_create import Users, Chats, Messages, session_create
from db_modules.db_query import check_user


def create_chat(login:str,chat:str):
    user=check_user(login=login)
    if user==True:
        session = session_create()
        try:
            create_chat_query = Chats(user_login=login, chat_name=chat)
            session.add(create_chat_query)
            session.commit()
            result={'result':True, 'message':"Чат создан",'category':"success",'cod':201}
            logger.debug(f"Создан чат пользователем {login}")
        except Exception as err:
            result={'result':False, 'message':"Ошибка сервера чат не создан",'category':"warning",'cod':500}
            logger.error(f"Не удалось создать чат пользователя {login} Ошибка {err}")
        finally:
            session.close()
    else:
        result={'result':False, 'message':"Чат не создан из-за отсутсвия пользователя в базе",'category':"warning",'cod':404}
    return result



def get_chats(login):
    session = db.session
    try:
        user_chats = session.scalars(
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
                select(Chats.id, Chats.chat_name).where(
                    (Chats.user_login == login) & (Chats.chat_del != True)
                )
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
        user = session.scalars(
            select(Users.login).where(Users.login == login)
        ).one_or_none()
        chat = session.scalars(
            select(Chats.id).where(Chats.id == chat_id)
        ).one_or_none()
        logger.trace(
            f"Проверка существования пользователя {login} и чата {chat_id} прошла успешно"
        )
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование пользователя {login} и чата {chat_id} Ошибка {err}"
        )
    if user == login and chat != None:
        try:
            add_message_query = Messages(user_login=login, chat_id=chat_id, text=text)
            session.add(add_message_query)
            session.commit()
            logger.trace(f"Сообщение в чате {chat_id} создано")
        except Exception as err:
            logger.error(f"Не удалось записать сообщение в чат {chat_id} Ошибка {err}")
    session.close()


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


def get_messages_ai(chat_id):
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
        ai_name = get_config_ai(name="ai_name")
        system_promt=str(get_config_ai(name='system_promt')).format(name=ai_name)
        result = [{"role":"system","content":system_promt}]
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
        user = session.scalars(
            select(Users.login).where(Users.login == login)
        ).one_or_none()
        chat = session.scalars(
            select(Chats.id).where(Chats.id == chat_id)
        ).one_or_none()
        logger.trace(
            f"Проверка существования пользователя {login} и чата {chat_id} прошла успешно"
        )
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование пользователя {login} и чата {chat_id} Ошибка {err}"
        )
    if user == login and chat != None:
        try:
            messages_query = session.execute(
                select(
                    Users.chat_role,
                    Messages.id,
                    Messages.text,
                )
                .where(Messages.chat_id == chat_id)
                .join(Users)
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
            result = False
    else:
        result = False
    session.close()
    return result


def get_delet_chats_irrevocably():
    session = db.session
    try:
        result = list()
        chats = session.execute(
            select(Chats.id, Chats.chat_name,Chats.user_login).where(Chats.chat_del == True)
        ).all()
        for chat in chats:
            chat_dict={'chat_id':chat[0],'chat_name':chat[1],'user':chat[2]}
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
            logger.error(f"Не удалось проверить наличие чатa {chat} для удаления Ошибка {err}")
        if check_del != None:
            try:
                session.execute(delete(Chats).where((Chats.chat_del==True) & (Chats.id==chat)))
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
            logger.error(f"Не удалось проверить наличие чатa {chat} для удаления Ошибка {err}")
        if check_del != None:
            try:
                session.execute(update(Chats).where((Chats.chat_del==True) & (Chats.id==chat)).values(chat_del=False))
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
