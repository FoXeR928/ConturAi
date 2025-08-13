from sqlalchemy import select,update
from loguru import logger

from db_modules.db_create import Users, session_create, Token_API


def auth_query(login:str, password:str):
    session = session_create()
    try:
        auth = session.scalars(select(Users).where(Users.login == login)).one()
        check_auth = auth.check_password(password=password)
        logger.debug(f"Авторизация пользователя {login} прошла успешно")
    except Exception as err:
        session.close()
        logger.error(f"Не удалось авторизировать пользователя {login} Ошибка {err}")
        return {'result':False,'message':"Ошибка сервера авторизация не удалась", 'category':"error",'cod':500}
    if check_auth==True:
        try:
            auth.generate_token()
            session.commit()
            token=session.scalars(select(Users.token).where(Users.login == login)).one()
            logger.debug(f"Токен пользователя {login} успешно сгенерирован")
            result={'result':True,'token':token,'message':"Авторизация прошла успешно", 'category':"success",'cod':200}
        except Exception as err:
            logger.error(f"Не удалось авторизировать пользователя {login} Ошибка {err}")
            return {'result':False,'message':"Ошибка сервера авторизация не удалась", 'category':"error",'cod':500}
        finally:
            session.close()
    else:
        result={'result':False,'message':"Неверный логин или пароль", 'category':"warning",'cod':401}
    return result

def logout_query(login:str):
    session = session_create()
    try:
        session.execute(update(Users).where(Users.login==login).values(token=None))
        session.commit()
        result={'result':True,'message':"Пользователь деавторизирован", 'category':"success",'cod':201}
        logger.debug(f'Пользователь {login} деавторизирован')
    except Exception as err:
        logger.error(f"Не удалось деавторизировать пользователя {login} Ошибка {err}")
        return {'result':False,'message':"Ошибка сервера деавторизация не удалась", 'category':"error",'cod':500}
    finally:
        session.close()
    return result

def get_token_query():
    session = session_create()
    try:
        token_get=session.scalars(select(Token_API.token).where(Token_API.id == 1)).one_or_none()
        if token_get!=None:
            result={'result':True, 'token_api':token_get,'message':"Токен получен",'category':"success",'cod':200}
        else:
            result={'result':False, 'message':"Токен не создан", 'category':"warning",'cod':200}
    except Exception as err:
        logger.error(f"Не удалось получить токен Ошибка {err}")
        return {'result':False,'message':"Ошибка сервера", 'category':"error",'cod':500}
    finally:
        session.close()
    return result
    
def create_token_query():
    session = session_create()
    try:
        token_get=session.scalars(select(Token_API).where(Token_API.id == 1)).one_or_none()
        if token_get==None:
            session.add(Token_API(token=None))
            token_get=session.scalars(select(Token_API).where(Token_API.id == 1)).one_or_none()
            token_get.generate_token()
            session.commit()
        else:
            token_get.generate_token()
        token_get=session.scalars(select(Token_API.token).where(Token_API.id == 1)).one_or_none()
        result={'result':True, 'token_api':token_get,'message':"Токен создан",'category':"success",'cod':201}
    except Exception as err:
        logger.error(f"Не удалось создания токена токен Ошибка {err}")
        return {'result':False,'message':"Ошибка сервера при создания токена", 'category':"error",'cod':500}
    finally:
        session.close()
    return result