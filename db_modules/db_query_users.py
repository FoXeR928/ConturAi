from sqlalchemy import select, update, delete, func
from loguru import logger

from db_modules.db_create import Users, session_create
from db_modules.db_query import check_user
from api.api_auth import User


def check_user_opportunity(user: str, login: str):
    session = session_create
    try:
        user_check = session.scalars(
            select(Users.user_role).where(Users.login == login)
        ).one()
        if user_check == "admin":
            admins = session.scalar(
                select(func.count(Users.login)).where(Users.user_role == "admin")
            )
            if admins == 1:
                if user == login:
                    result = False
                else:
                    result = True
            else:
                result = True
        else:
            result = True
        logger.trace("Количество администраторов проверено успешно")
    except Exception as err:
        result = False
        logger.error(f"Не удалось проверить количество администраторов Ошибка {err}")
    finally:
        session.close()
    return result


def get_users_query():
    session = session_create
    try:
        users_get = session.execute(
            select(
                Users.login,
                Users.user_name,
                Users.user_role,
                Users.disabled,
                Users.date_create,
                Users.date_update,
            ).where(Users.user_role != "system")
        ).all()
        users = [row._mapping for row in users_get]
        result = {
            "result": True,
            "message": "Пользователи получены",
            "users": users,
            "category": "success",
            "cod": 200,
        }
        logger.debug("Получение списка пользователей системы прошло успешно")
    except Exception as err:
        logger.error(f"Не удалось получить список пользователей системы Ошибка {err}")
        result = {
            "result": False,
            "message": "Ошибка сервера не удалось получить пользователей",
            "category": "error",
            "cod": 500,
        }
    finally:
        session.close()
    return result


def registration_user_query(login: str, user_name: str, password: str):
    if check_user(login=login) == False:
        try:
            session = session_create
            add_user_query = Users(login=login, user_name=user_name)
            add_user_query.set_password(password)
            session.add(add_user_query)
            session.commit()
            result = {
                "result": True,
                "message": "Пользователь создан",
                "category": "success",
                "cod": 201,
            }
            logger.success(f"Пользователь {login} создан")
        except Exception as err:
            result = {
                "result": False,
                "message": "Ошибка сервера пользователь не создан",
                "category": "error",
                "cod": 500,
            }
            logger.error(f"Не удалось создать пользователя {login} Ошибка {err}")
        finally:
            session.close()
    else:
        result = {
            "result": False,
            "message": "Пользователь уже создан",
            "category": "warning",
            "cod": 409,
        }
        logger.info(f"Пользователь {login} не создан так как уже есть в базе")
    return result


def update_password_user_query(user_update: User, login: str, password: str):
    if check_user(login=login) == True:
        if user_update.login == login or user_update.role == "admin":
            session = session_create
            try:
                user = session.query(Users).filter(Users.login == login).one()
                user.set_password(password)
                session.commit()
                result = {
                    "result": True,
                    "message": "Пароль изменен",
                    "category": "success",
                    "cod": 201,
                }
                logger.success(
                    f"Изменен пароль пользователя {login} пользователем {user_update.login}"
                )
            except Exception as err:
                result = {
                    "result": False,
                    "message": "Ошибка сервера пароль не изменен",
                    "category": "error",
                    "cod": 500,
                }
                logger.error(
                    f"Не удалось обновить пароль пользователя {login} Ошибка {err}"
                )
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
            "message": "Не найден пользователь",
            "category": "warning",
            "cod": 404,
        }
    return result


def update_role_user_query(user_update: User, login: str, role: str):
    if check_user(login=login) == True:
        if role == "user":
            opportunity = check_user_opportunity(user=user_update.login, login=login)
        else:
            opportunity = True
        if opportunity == True:
            session = session_create
            try:
                session.execute(
                    update(Users).where(Users.login == login).values(user_role=role)
                )
                session.commit()
                result = {
                    "result": True,
                    "message": "Роль изменена",
                    "category": "success",
                    "cod": 201,
                }
                logger.success(
                    f"Изменена роль пользователя {login} пользователем {user_update.login}"
                )
            except Exception as err:
                result = {
                    "result": False,
                    "message": "Ошибка сервера роль не изменена",
                    "category": "error",
                    "cod": 500,
                }
                logger.error(
                    f"Не удалось обновить роль пользователя {login} Ошибка {err}"
                )
            finally:
                session.close()
        else:
            result = {
                "result": False,
                "message": "Нельзя изменить роль из-за отсутсвия других администраторов",
                "category": "warning",
                "cod": 403,
            }
    else:
        result = {
            "result": False,
            "message": "Не найден пользователь",
            "category": "warning",
            "cod": 404,
        }
    return result


def delete_user_query(user_delet: User, login: str):
    if check_user(login=login) == True:
        if check_user_opportunity(user=user_delet.login, login=login) == True:
            session = session_create
            try:
                session.execute(delete(Users).where(Users.login == login))
                session.commit()
                result = {
                    "result": True,
                    "message": "Пользователь удален",
                    "category": "success",
                    "cod": 201,
                }
                logger.success(
                    f"Пользоваватель {login} удален пользователем {user_delet.login}"
                )
            except Exception as err:
                result = {
                    "result": False,
                    "message": "Ошибка сервера роль не изменена",
                    "category": "error",
                    "cod": 500,
                }
                logger.error(f"Не удалось удалить пользователя {login} Ошибка {err}")
            finally:
                session.close()
        else:
            result = {
                "result": False,
                "message": "Нельзя удалить пользователя из-за отсутсвия других администраторов",
                "category": "warning",
                "cod": 403,
            }
    else:
        result = {
            "result": False,
            "message": "Не найден пользователь",
            "category": "warning",
            "cod": 404,
        }
    return result
