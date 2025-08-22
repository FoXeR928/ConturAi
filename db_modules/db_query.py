from sqlalchemy import select
from loguru import logger

from db_modules.db_create import Users, session_create


def check_user(login: str):
    session = session_create()
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


def user_auth_check(login: str, token: str):
    session = session_create()
    try:
        user_token = session.scalars(select(Users).where(Users.login == login)).one()
        logger.trace(f"Проверка токена пользователя {login} в базе")
        result = user_token.check_token(token)
        logger.debug(f"Проверка токена пользователя {login} в базе прошла успешно")
    except Exception as err:
        logger.error(f"Не удалось проверить токен пользователя {login} Ошибка {err}")
        result = False
    finally:
        session.close()
    return result


def admin_auth_check(login: str, token: str):
    session = session_create()
    try:
        user_token = session.scalars(select(Users).where(Users.login == login)).one()
        logger.trace(f"Проверка токена пользователя {login} в базе")
        result = user_token.check_admin(token)
        logger.debug(f"Проверка токена пользователя {login} в базе прошла успешно")
    except Exception as err:
        logger.error(f"Не удалось проверить токен пользователя {login} Ошибка {err}")
        result = False
    finally:
        session.close()
    return result
