from flask_login import login_user
from flask import flash
from sqlalchemy import select
from loguru import logger

from db.db_create import Users, db


def auth_query(login, password, remember):
    session = db.session
    try:
        user = session.scalars(
            select(Users).where(Users.login == login)
        ).one_or_none()
        logger.debug(f"Проверка пользователя {login} в базе для авторизации")
    except Exception as err:
        logger.error(f"Не удалось проверить пользователя {login} Ошибка {err}")
    if not (user == None):
        try:
            auth = session.scalars(select(Users).where(Users.login==login)).one()
            check_auth = auth.check_password(password=password)
            print(check_auth)
            logger.success(f"Авторизация пользователя {login} прошла успешно")
        except Exception as err:
            logger.error(f"Не удалось авторизировать пользователя {login} Ошибка {err}")
        if check_auth:
            login_user(user=auth,remember=remember)
            flash(message="Неверный логин или пароль", category="warning")
            result=True
        else:
            flash(message="Авторизация прошла успешно", category="success")
            result=False
    else:
        flash(message="Неверный логин или пароль", category="warning")
        result=True
    session.close()
    return result

