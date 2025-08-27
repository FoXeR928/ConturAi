from sqlalchemy import select, update, delete, func
from loguru import logger

from db_modules.db_create import Users, session_create
from db_modules.db_query import check_user


def get_users_query():
    session = session_create()
    try:
        users_get = session.execute(
            select(Users.login, Users.user_name, Users.user_role, Users.disabled,Users.date_create,Users.date_update).where(
                Users.user_role != "system"
            )
        ).all()
        users=[row._mapping for row in users_get]
        result = {
            "result": True,
            "message": "Чаты на удаление получены",
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

def registration_user_query(login:str, user_name:str,password:str):
    user=check_user(login=login)
    if user == False:
        try:
            session = session_create()
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
    

def update_password_user(user_update_password, login, password):
    session = db.session
    try:
        user = session.query(Users).filter(Users.login == login).one()
        user.set_password(password)
        session.commit()
        logger.success(
            f"Изменен пароль пользователя {login} пользователем {user_update_password}"
        )
    except Exception as err:
        logger.error(f"Не удалось обновить пароль пользователя {login} Ошибка {err}")
    session.close()


def add_user_status(login, role):
    session = db.session
    try:
        user_role = session.scalars(
            select(Users.user_role).where(Users.login == login)
        ).one_or_none()
        logger.trace(f"Проверка существование пользователя {login}")
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование пользователя {login} Ошибка {err}"
        )
    if user_role != None:
        try:
            admins = session.scalar(
                select(func.count(Users.login)).where(Users.user_role == "admin")
            )
            if user_role == "admin":
                if admins <= 1:
                    logger.warning(
                        f"У администратора {login} нельзя изменить роль, так как существует только 1 запись админа"
                    )
                    flash(
                        message="Нельзя изменить роль учетной запис, так как существует только 1 запись админа",
                        category="warning",
                    )
                    return False
            session.execute(
                update(Users).where(Users.login == login).values(user_role=role)
            )
            session.commit()
            logger.success(f"Роль пользовавателя {login} обнавлена на {role}")
            flash(message="Роль пользователя изменена", category="success")
        except Exception as err:
            logger.error(f"Не удалось изменить роль пользователя {login} Ошибка {err}")
            flash(message="Не удалось изменить роль пользователя", category="error")
    else:
        logger.warning(
            f"Не удалось изменить роль пользователя {login} Ошибка отсутсвие пользователя"
        )
        flash(message="Не удалось найти пользователя ", category="error")
    session.close()


def delet_user(login):
    session = db.session
    try:
        user = session.scalars(
            select(Users.user_role).where(Users.login == login)
        ).one_or_none()
        logger.trace(f"Проверка существование пользователя {login}")
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование пользователя {login} Ошибка {err}"
        )
    if not (user == None):
        try:
            admins = session.scalar(
                select(func.count(Users.login)).where(Users.user_role == "admin")
            )
            if user == "admin":
                if admins <= 1:
                    logger.warning(
                        f"Администратора {login} нельзя удалить, так как существует только 1 запись админа"
                    )
                    flash(
                        message="Нельзя удалить учетную запись админа, так как существует только 1 запись админа",
                        category="warning",
                    )
                    return False
                else:
                    logger.info(f"Администратора {login} отправлен на удаление")
            session.execute(delete(Users).where(Users.login == login))
            session.commit()
            logger.success(f"Пользоваватель {login} удален")
            flash(message="Пользоваватель удален", category="success")
        except Exception as err:
            logger.error(f"Не удалось удалить пользователя {login} Ошибка {err}")
            flash(message="Не удалось удалить пользователя", category="error")
    else:
        logger.warning(
            f"Не удалось удалить пользователя {login} Ошибка отсутсвие пользователя"
        )
        flash(message="Не удалось найти пользователя ", category="error")
    session.close()
