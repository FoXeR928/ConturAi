from sqlalchemy import select, update
from datetime import datetime, timedelta
import jwt
from loguru import logger

from db_modules.db_create import Users, session_create, Token_API
from db_modules.db_query import check_user
from db_modules.db_query_config import get_config


def create_token(data: dict, expires_use: bool = False):
    try:
        expire = datetime.utcnow()
        if expires_use == True:
            expire += timedelta(days=7)
        else:
            expire += timedelta(minutes=30)
        data["exp"] = expire
        encoded_jwt = jwt.encode(
            payload=data, key=get_config(name="skey"), algorithm="HS256"
        )
        result = encoded_jwt
        logger.debug(f"Токен создан для пользователя {data['sub']}")
    except Exception as err:
        logger.error(f"Ошибка сервера создания токена: {err}")
        raise False
    return result


def decode_token(token: str):
    payload = jwt.decode(jwt=token, key=get_config(name="skey"), algorithms="HS256")
    user = payload.get("sub")
    return user


def get_current_user_query(login: str):
    if check_user(login=login) == True:
        session = session_create()
        try:
            user = session.execute(
                select(Users.login, Users.user_name, Users.user_role).where(
                    Users.login == login
                )
            ).one_or_none()
            result = user
        except Exception as err:
            logger.error(
                f"Не удалось получить данные пользователя {login} Ошибка {err}"
            )
            result = None
        finally:
            session.close()
    else:
        result = None
    return result


def auth_query(login: str, password: str):
    result_no_auth = {
        "result": False,
        "message": "Неверный логин или пароль",
        "category": "warning",
        "cod": 401,
    }
    result_error = {
        "result": False,
        "message": "Ошибка сервера авторизация не удалась",
        "category": "error",
        "cod": 500,
    }
    if check_user(login=login) == True:
        session = session_create()
        try:
            auth = session.scalars(select(Users).where(Users.login == login)).one()
            check_auth = auth.check_password(password=password)
            logger.debug(f"Авторизация пользователя {login} прошла успешно")
        except Exception as err:
            session.close()
            logger.error(f"Не удалось авторизировать пользователя {login} Ошибка {err}")
            raise result_error
        finally:
            session.close()
        if check_auth == True:
            token = create_token(data={"sub": login})
            if token != False:
                result = {
                    "result": True,
                    "access_token": token,
                    "token_type": "bearer",
                    "message": "Авторизация прошла успешно",
                    "category": "success",
                    "cod": 200,
                }
            else:
                result = result_error
        else:
            result = result_no_auth
    else:
        result = result_no_auth
    return result


def logout_query(login: str):
    session = session_create()
    try:
        session.execute(update(Users).where(Users.login == login).values(token=None))
        session.commit()
        result = {
            "result": True,
            "message": "Пользователь деавторизирован",
            "category": "success",
            "cod": 201,
        }
        logger.debug(f"Пользователь {login} деавторизирован")
    except Exception as err:
        logger.error(f"Не удалось деавторизировать пользователя {login} Ошибка {err}")
        return {
            "result": False,
            "message": "Ошибка сервера деавторизация не удалась",
            "category": "error",
            "cod": 500,
        }
    finally:
        session.close()
    return result


def get_token_query():
    session = session_create()
    try:
        token_get = session.execute(
            select(Token_API.token, Token_API.date_create).where(Token_API.id == 1)
        ).one_or_none()
        if token_get != None:
            result = {
                "result": True,
                "token_api": token_get[0],
                "date_create": token_get[1],
                "message": "Токен получен",
                "category": "success",
                "cod": 200,
            }
        else:
            result = {
                "result": False,
                "message": "Токен не создан",
                "category": "warning",
                "cod": 200,
            }
    except Exception as err:
        logger.error(f"Не удалось получить токен Ошибка {err}")
        return {
            "result": False,
            "message": "Ошибка сервера",
            "category": "error",
            "cod": 500,
        }
    finally:
        session.close()
    return result


def create_token_query():
    session = session_create()
    try:
        token_get = session.scalars(
            select(Token_API).where(Token_API.id == 1)
        ).one_or_none()
        token_get.generate_token()
        session.commit()
        token_get = session.scalars(
            select(Token_API.token).where(Token_API.id == 1)
        ).one_or_none()
        result = {
            "result": True,
            "token_api": token_get,
            "message": "Токен создан",
            "category": "success",
            "cod": 201,
        }
    except Exception as err:
        logger.error(f"Не удалось создания токена токен Ошибка {err}")
        return {
            "result": False,
            "message": "Ошибка сервера при создания токена",
            "category": "error",
            "cod": 500,
        }
    finally:
        session.close()
    return result
