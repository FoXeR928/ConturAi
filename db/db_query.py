from sqlalchemy import select
from loguru import logger

from db.db_create import Users,db


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


def get_user_role(login):
    session = db.session
    try:
        user_role = session.execute(
            select(Users.user_role).where(Users.login == login)
        ).one_or_none()
        logger.trace(f"Получена роль пользователя {login}")
    except Exception as err:
        logger.error(
            f"Не удалось получение роль пользователя {login} Ошибка {err}"
        )
    if not (user_role == None) and user_role.user_role == "admin":
        result = True
    else:
        result = False
    session.close()
    return result


def auth_query(login, password):
    session = db.session
    try:
        user = session.execute(
            select(Users.login).where(Users.login == login)
        ).one_or_none()
        logger.debug(f"Проверка пользователя {login} в базе для авторизации")
    except Exception as err:
        logger.error(f"Не удалось проверить пользователя {login} Ошибка {err}")
    if not (user == None):
        try:
            login_base = Users.query.filter_by(login=login).first()
            result = login_base.check_password(password)
            logger.success(f"Авторизация пользователя {login} прошла успешно")
        except Exception as err:
            logger.error(f"Не удалось авторизировать пользователя {login} Ошибка {err}")
    session.close()
    return result
