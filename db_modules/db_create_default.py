from sqlalchemy import select, delete, func
from loguru import logger
import secrets

from db_modules.db_create import Users, Configs, Configs_ai, session_create


def create_default_users(
    recreate: bool = False,
    admin_login: str = "admin",
    admin_password: str = "admin",
    admin_name: str = "админ",
    system_login: str = "system",
    system_chat_role: str = "assistant",
):
    session = session_create
    base = Users
    if recreate:
        try:
            session.execute(delete(base))
            session.commit()
            logger.info("Удалены строки таблицы Users")
        except Exception as err:
            logger.error(f"Не удалось удалить строки таблицы Users Ошибка {err}")
    add_list = list()
    try:
        check_admin = session.scalar(
            select(func.count(base.login)).where(base.isAdmin == True)
        )
        check_system = session.scalars(
            select(base).where(base.login == system_login)
        ).first()
        logger.trace("Проверенно существование записей в базе Users")
    except Exception as err:
        logger.error(
            f"Не удалось проверить существование записей таблицы Users Ошибка {err}"
        )
    print(check_admin)
    if check_admin == 0:
        try:
            admin = base(login=admin_login, user_name=admin_name,isAdmin=True)
            admin.set_password(admin_password)
            add_list.append(admin)
            logger.debug(f"Создан запрос на добавление {admin_login} в базу Users")
        except Exception as err:
            logger.error(
                f"Не удалось создать запрос на добавление {admin_login} в базу Users Ошибка {err}"
            )
    if check_system == None:
        try:
            system = base(
                login=system_login,
                chat_role=system_chat_role,
                isSystem=True
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
    recreate: bool = False,
    app_port: int = 7000,
    token: str = secrets.token_hex(64),
    front_enable: bool = True,
    site_name: str = "Ragi_AI",
    debug: bool = False,
    pdf: str = "application/pdf",
    word: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    excel: str = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
):
    configs_list = (
        ("app_port", "Порт приложения", app_port, "number"),
        ("skey", "Ключ для генерации OAuth2 токена", token, "text"),
        ("front_enable", "Включение веб-интерфейса", front_enable, "boolen"),
        ("site_name", "Имя приложения", site_name, "text"),
        ("debug", "Подробное логирование", debug, "boolen"),
        ("pdf", "Параметр отвечающий за формат PDF", pdf, "text"),
        ("word", "Параметр отвечающий за формат WORD", word, "text"),
        ("excel", "Параметр отвечающий за формат EXCEL", excel, "text"),
    )
    session = session_create
    base = Configs
    if recreate:
        try:
            session.execute(delete(base))
            session.commit()
            logger.info("Удалены строки таблицы Configs")
        except Exception as err:
            logger.error(f"Не удалось удалить строки таблицы Configs Ошибка {err}")
    add_list = list()
    for configs in configs_list:
        try:
            check_config = session.scalars(
                select(base).where(base.name == configs[0])
            ).one_or_none()
            logger.trace(
                f"Проверенно существование записи {configs[0]} в таблице Configs"
            )
        except Exception as err:
            logger.error(
                f"Не удалось проверить существование записи {configs[0]} в таблице Configs Ошибка {err}"
            )
        if check_config == None:
            try:
                config = base(
                    name=configs[0],
                    about=configs[1],
                    value=configs[2],
                    input_format=configs[3],
                )
                add_list.append(config)
                logger.debug(f"Создан запрос на добавление конфига в базу Configs")
            except Exception as err:
                logger.error(
                    f"Не удалось создать запрос на добавление в базу Configs Ошибка {err}"
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


def create_default_config_ai(
    recreate: bool = False,
    ai_name: str = "Раги",
    system_promt: str = "Ты - {name}, твоя задача отвечать на вопросы используя информации из базы, а если информации нет генерировать ответ самостоятельно и добавлять 'Ответ сгенерирован самостоятельно'",
    promt: str = "Контекст: {context} Вопрос: {quest}",
    search_rag: int = 5,
    batch_size: int = 256,
):
    configs_list = (
        ("ai_name", "Параметр отвечающий за имя нейросети", ai_name, "text"),
        (
            "system_promt",
            "Параметр отвечающий за промт для нейросети",
            system_promt,
            "textarea",
        ),
        (
            "promt",
            "Параметр отвечающий за промт вопроса для нейросети",
            promt,
            "textextarea",
        ),
        ("search_rag", "Лимит поиска по RAG базе", search_rag, "number"),
        ("batch_size", "Размер чанков для загрузки в RAG базу", batch_size, "number"),
    )
    session = session_create
    base = Configs_ai
    if recreate:
        try:
            session.execute(delete(base))
            session.commit()
            logger.info("Удалены строки таблицы Configs_ai")
        except Exception as err:
            logger.error(f"Не удалось удалить строки таблицы Configs_ai Ошибка {err}")
    add_list = list()
    for configs in configs_list:
        try:
            check_config = session.scalars(
                select(base).where(base.name == configs[0])
            ).one_or_none()
            logger.trace(
                f"Проверенно существование записи {configs[0]} в таблице Configs_ai"
            )
        except Exception as err:
            logger.error(
                f"Не удалось проверить существование записи {configs[0]} в таблице Configs_ai Ошибка {err}"
            )
        if check_config == None:
            try:
                config = base(
                    name=configs[0],
                    about=configs[1],
                    value=configs[2],
                    input_format=configs[3],
                )
                add_list.append(config)
                logger.debug(f"Создан запрос на добавление конфига в базу Configs_ai")
            except Exception as err:
                logger.error(
                    f"Не удалось создать запрос на добавление в базу Configs_ai Ошибка {err}"
                )
    if len(add_list) != 0:
        try:
            session.add_all(add_list)
            session.commit()
            logger.info("Добавлены конфиги AI по умолчанию")
        except Exception as err:
            logger.error(
                f"Не удалось добавить конфиги по умолчанию в базу Configs_ai Ошибка {err}"
            )
            exit()
    else:
        logger.debug("Конфиги по умолчанию уже в базе есть")
    session.close()
