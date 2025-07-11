from sqlalchemy import select, update
from loguru import logger

from db.db_create import Users, Files, Configs,db


# Users
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
    check_user=session.execute(select(Users.login).where(Users.login==login)).one_or_none()
    if check_user==None:
        try:
            add_user_query = Users(login=login, user_name=user_name)
            add_user_query.set_password(password)
            session.add(add_user_query)
            session.commit()
            logger.success(f"Пользователь {login} создан")
        except Exception as err:
            logger.error(f"Не удалось создать пользователя {login} Ошибка {err}")
        session.close()
    else:
        logger.info(f'Пользователь {login} не создан так как уже есть в базе')


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
        except Exception as err:
            logger.error(f"Не удалось изменить роль пользователя {login} Ошибка {err}")
    session.close()


# Files
def add_file(file, filetype, file_name):
    session=db.session
    try:
        check_file=session.execute(select(Files.file_name).where(file_name=file_name)).one_or_none
        logger.trace(f'Проверино на личие файл {file_name}')
    except Exception as err:
        logger.warning(f"Не проверить существование файла {file_name} Ошибка {err}")
    if check_file==None:
        try:
            create_file = Files(file_name=file_name, file_type=filetype, file=file.read())
            session.add(create_file)
            session.commit()
            logger.success(f"Файл {file_name} добавлен в базу")
        except Exception as err:
            logger.error(f"Не удалось добавить файл {file_name} Ошибка {err}")
    else:
        try:
            session.execute(update(Files).where(Files.file_name==file_name).values(file_type=filetype,file=file.read()))
            session.commit
            logger.success(f"Файл {file_name} обнавлен в базе")
        except Exception as err:
            logger.error(f"Не удалось обновить файл {file_name} в базе Ошибка {err}")


# Config
def get_configs():
    session = db.session
    try:
        search_config = session.execute(
            select(Configs.name, Configs.about, Configs.value)
        ).all()
        result = list()
        for config in search_config:
            result.append(
                {"name": config.name, "about": config.about, "value": config.value}
            )
        logger.trace(f"Получен список конфигов из базы")
    except Exception as err:
        logger.error(f"Не удалось получить список конфигов из базы Ошибка {err}")
    session.close()
    return result


def get_config(name):
    session = db.session
    try:
        search_config = session.execute(
            select(Configs.value).where(Configs.name == name)
        ).first()
        result = search_config.value
        logger.debug(f"Получено значения конфигова {name} из базы")
    except Exception as err:
        logger.error(
            f"Не удалось получить значения конфигова {name} из базы Ошибка {err}"
        )
        result = None
    session.close()
    return result


def update_config(name, value):
    session = db.session
    try:
        session.execute(
            update(Configs).where(Configs.name == name).values(value=value)
        )
        session.commit()
        logger.success(f"Обноваление значения конфигова {name} на {value} из базы")
    except Exception as err:
        logger.error(f"Не удалось обновить значения конфигова {name} Ошибка {err}")
    session.close()
