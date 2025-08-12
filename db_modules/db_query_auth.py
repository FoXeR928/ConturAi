from sqlalchemy import select
from loguru import logger

from db_modules.db_create import Users, session_create


def auth_query(login, password):
    session = session_create()
    try:
        user = session.scalars(select(Users).where(Users.login == login)).one_or_none()
        logger.debug(f"Проверка пользователя {login} в базе для авторизации")
    except Exception as err:
        logger.error(f"Не удалось проверить пользователя {login} Ошибка {err}")
        return {'result':False,'message':"Ошибка сервера авторизация не удалась", 'category':"error",'cod':500}
    if not (user == None):
        try:
            auth = session.scalars(select(Users).where(Users.login == login)).one()
            check_auth = auth.check_password(password=password)
            logger.debug(f"Авторизация пользователя {login} прошла успешно")
        except Exception as err:
            logger.error(f"Не удалось авторизировать пользователя {login} Ошибка {err}")
            return {'result':False,'message':"Ошибка сервера авторизация не удалась", 'category':"error",'cod':500}
        if check_auth:
            try:
                auth.generate_token()
                token=session.scalars(select(Users.token).where(Users.login == login)).one()
                logger.debug(f"Токен пользователя {login} успешно сгенерирован")
                result={'result':True,'token':token,'message':"Авторизация прошла успешно", 'category':"success",'cod':200}
            except Exception as err:
                logger.error(f"Не удалось авторизировать пользователя {login} Ошибка {err}")
                return {'result':False,'message':"Ошибка сервера авторизация не удалась", 'category':"error",'cod':500}
        else:
            result={'result':False,'message':"Неверный логин или пароль", 'category':"warning",'cod':401}
    else:
        result={'result':False,'message':"Неверный логин или пароль", 'category':"warning",'cod':401}
    session.close()
    return result
