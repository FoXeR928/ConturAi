from sqlalchemy import select, update, delete, func
from loguru import logger
from flask import flash

from db.db_create import Users, db


def get_user_role(login):
    session = db.session
    try:
        user_check = session.scalars(
            select(Users.user_role).where(Users.login == login)
        ).one_or_none()
        logger.trace(f"Проверено существование пользователя {login}")
    except Exception as err:
        logger.error(
            f"Не удалось проверить существование пользователя {login} Ошибка {err}"
        )
    if not (user_check == None):
        try:
            user_role = session.execute(
                select(Users.user_role).where(Users.login == login)
            ).one()
            if user_role.user_role == "admin":
                result = True
            else:
                result = False
        except Exception as err:
            logger.error(f"Не удалось получение роль пользователя {login} Ошибка {err}")
    else:
        result = False
    session.close()
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


def get_users():
    session = db.session
    result = list()
    try:
        users = session.execute(
            select(Users.login, Users.user_name, Users.user_role).where(
                Users.user_role != "system"
            )
        ).all()
        for user in users:
            result.append(
                {"login": user[0], "user_name": user[1], "user_role": user[2]}
            )
        logger.debug("Получение списка пользователей системы прошло успешно")
    except Exception as err:
        logger.error(f"Не удалось получить список пользователей системы Ошибка {err}")
    session.close()
    return result


def reg_user(login, password, user_name):
    session = db.session
    check_user = session.execute(
        select(Users.login).where(Users.login == login)
    ).one_or_none()
    if check_user == None:
        try:
            add_user_query = Users(login=login, user_name=user_name)
            add_user_query.set_password(password)
            session.add(add_user_query)
            session.commit()
            flash(message="Пользователь создан", category="success")
            logger.success(f"Пользователь {login} создан")
        except Exception as err:
            logger.error(f"Не удалось создать пользователя {login} Ошибка {err}")
            flash(message="Пользователь не создан", category="error")
    else:
        logger.info(f"Пользователь {login} не создан так как уже есть в базе")
        flash(
            message="Пользователь не создан так как уже есть в базе", category="warning"
        )
    session.close()


def add_user_status(login, role):
    session = db.session
    try:
        user_role = session.execute(
            select(Users.login).where(Users.login == login)
        ).one_or_none()
        logger.trace(f"Проверка существование пользователя {login}")
    except Exception as err:
        logger.warning(
            f"Не удалось проверить существование пользователя {login} Ошибка {err}"
        )
    if not (user_role == None):
        try:
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
        user = session.scalars(select(Users).where(Users.login == login)).one_or_none()
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
            print(admins)
            if admins <= 1:
                session.execute(delete(Users).where(Users.login == login))
                session.commit()
                logger.success(f"Пользоваватель {login} удален")
                flash(message="Пользоваватель удален", category="success")
            else:
                flash(
                    message="Нельзя удалить учетную запись админа, так как существует только 1 запись админа ",
                    category="warning",
                )
        except Exception as err:
            logger.error(f"Не удалось удалить пользователя {login} Ошибка {err}")
            flash(message="Не удалось удалить пользователя", category="error")
    else:
        logger.warning(
            f"Не удалось удалить пользователя {login} Ошибка отсутсвие пользователя"
        )
        flash(message="Не удалось найти пользователя ", category="error")
    session.close()
