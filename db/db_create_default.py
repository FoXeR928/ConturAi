from sqlalchemy import select, delete
from loguru import logger

from db.db_create import Users, Configs, db
from db.db_query_config import get_config


def create_default_users(
    recreate=False,
    admin_login="admin",
    admin_password="admin",
    admin_name="админ",
    admin_role="admin",
    system_login='system',
    system_role='system'
):
    session = db.session
    if recreate:
        try:
            session.execute(delete(Users))
            session.commit()
            logger.info("Удалены строки таблицы Users")
        except Exception as err:
            logger.error(f"Не удалось удалить строки таблицы Users Ошибка {err}")
    add_list = list()
    system_chat_role=get_config('ai_role')
    system_name=get_config('ai_name')
    try:
        check_admin = session.scalars(
            select(Users).where(Users.login == admin_login)
        ).first()
        check_system = session.scalars(
            select(Users).where(Users.login == system_login)
        ).first()
        logger.trace("Проверенно существование записей в базе Users")
    except Exception as err:
        logger.error(
            f"Не удалось проверить существование записей таблицы Users Ошибка {err}"
        )
    if check_admin == None:
        try:
            admin = Users(login=admin_login, user_name=admin_name, user_role=admin_role)
            admin.set_password(admin_password)
            add_list.append(admin)
            logger.debug(f"Создан запрос на добавление {admin_login} в базу Users")
        except Exception as err:
            logger.error(
                f"Не удалось создать запрос на добавление {admin_login} в базу Users Ошибка {err}"
            )
    if check_system == None:
        try:
            system = Users(
                login=system_login,
                user_name=system_name,
                user_role=system_role,
                chat_role=system_chat_role,
            )
            add_list.append(system)
            logger.debug(f"Создан запрос на добавление {system_login} в базу Users")
        except Exception as err:
            logger.error(
                f"Не удалось создать запрос на добавление {system_login} в базу Users Ошибка {err}"
            )
    if len(add_list) != 0:
        try:
            session.add_all(add_list)
            session.commit()
            logger.info("Добавлены пользователи по умолчанию")
        except Exception as err:
            logger.error(
                f"Не удалось добавить пользователей по умолчанию в базу Users Ошибка {err}"
            )
            exit()
    else:
        logger.debug("Пользователи по умолчанию уже в базе есть")
    session.close()


def create_default_config(
    recreate=False,
    ai_role='system',
    ai_name='Раги',
    promt="Привет я ассистент {name}  База знаний: {context} Вопрос: {quest} Ответь используя базу знаний",
    pdf="application/pdf",
    word="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    excel="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
):
    session = db.session
    if recreate:
        try:
            session.execute(delete(Configs))
            session.commit()
            logger.info("Удалены строки таблицы Configs")
        except Exception as err:
            logger.error(f"Не удалось удалить строки таблицы Configs Ошибка {err}")
    add_list = list()
    try:
        check_ai_role = session.scalars(
            select(Configs).where(Configs.name == "ai_role")
        ).one_or_none()
        check_ai_name = session.scalars(
            select(Configs).where(Configs.name == "ai_name")
        ).one_or_none()
        check_promt = session.scalars(
            select(Configs).where(Configs.name == "ai_promt")
        ).one_or_none()
        check_format_pdf = session.scalars(
            select(Configs).where(Configs.name == "pdf")
        ).one_or_none()
        check_format_word = session.scalars(
            select(Configs).where(Configs.name == "word")
        ).one_or_none()
        check_format_excel = session.scalars(
            select(Configs).where(Configs.name == "excel")
        ).one_or_none()
        logger.trace("Проверенно существование записей в базе Configs")
    except Exception as err:
        logger.error(
            f"Не удалось проверить существование записей таблицы Configs Ошибка {err}"
        )
    if check_ai_role == None:
        try:
            config = Configs(
                name="ai_role",
                about="Параметр отвечающий за определение роли нейросети в чате",
                value=ai_role,
            )
            add_list.append(config)
            logger.debug(f"Создан запрос на добавление конфига роли нейросети в базу Configs")
        except Exception as err:
            logger.error(
                f"Не удалось создать запрос на добавление роли нейросети в базу Configs Ошибка {err}"
            )
    if check_ai_name == None:
        try:
            config = Configs(
                name="ai_name",
                about="Параметр отвечающий за имя нейросети",
                value=ai_name,
            )
            add_list.append(config)
            logger.debug(f"Создан запрос на добавление конфига имя нейросети в базу Configs")
        except Exception as err:
            logger.error(
                f"Не удалось создать запрос на добавление имя нейросети в базу Configs Ошибка {err}"
            )
    if check_promt == None:
        try:
            config = Configs(
                name="ai_promt",
                about="Параметр отвечающий за промт для нейросети",
                value=promt,
            )
            add_list.append(config)
            logger.debug(f"Создан запрос на добавление конфига промт в базу Configs")
        except Exception as err:
            logger.error(
                f"Не удалось создать запрос на добавление промт в базу Configs Ошибка {err}"
            )
    if check_format_pdf == None:
        try:
            config = Configs(
                name="pdf", about="Параметр отвечающий за формат PDF", value=pdf
            )
            add_list.append(config)
            logger.debug(f"Создан запрос на добавление конфига PDF в базу Configs")
        except Exception as err:
            logger.error(
                f"Не удалось создать запрос на добавление PDF в базу Configs Ошибка {err}"
            )
    if check_format_word == None:
        try:
            config = Configs(
                name="word", about="Параметр отвечающий за формат WORD", value=word
            )
            add_list.append(config)
            logger.debug(f"Создан запрос на добавление конфига WORD в базу Configs")
        except Exception as err:
            logger.error(
                f"Не удалось создать запрос на добавление WORD в базу Configs Ошибка {err}"
            )
    if check_format_excel == None:
        try:
            config = Configs(
                name="excel", about="Параметр отвечающий за формат EXCEL", value=excel
            )
            add_list.append(config)
            logger.debug(f"Создан запрос на добавление конфига EXCEL в базу Configs")
        except Exception as err:
            logger.error(
                f"Не удалось создать запрос на добавление EXCEL в базу Configs Ошибка {err}"
            )
    if len(add_list) != 0:
        try:
            session.add_all(add_list)
            session.commit()
            logger.info("Добавлены конфиги по умолчанию")
        except Exception as err:
            logger.error(
                f"Не удалось добавить конфиги по умолчанию в базу Configs Ошибка {err}"
            )
            exit()
    else:
        logger.debug("Конфиги по умолчанию уже в базе есть")
    session.close()
