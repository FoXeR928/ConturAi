from sqlalchemy import select, update, delete
from loguru import logger
from flask import flash

from db.db_create import Files, Configs, db



# Files
def add_file(file, filetype, file_name):
    session = db.session
    try:
        check_file = session.execute(
            select(Files.file_name).where(file_name=file_name)
        ).one_or_none
        logger.trace(f"Проверино на личие файл {file_name}")
    except Exception as err:
        logger.warning(f"Не проверить существование файла {file_name} Ошибка {err}")
    if check_file == None:
        try:
            create_file = Files(
                file_name=file_name, file_type=filetype, file=file.read()
            )
            session.add(create_file)
            session.commit()
            logger.success(f"Файл {file_name} добавлен в базу")
        except Exception as err:
            logger.error(f"Не удалось добавить файл {file_name} Ошибка {err}")
    else:
        try:
            session.execute(
                update(Files)
                .where(Files.file_name == file_name)
                .values(file_type=filetype, file=file.read())
            )
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
        session.execute(update(Configs).where(Configs.name == name).values(value=value))
        session.commit()
        logger.success(f"Обноваление значения конфигова {name} на {value} из базы")
    except Exception as err:
        logger.error(f"Не удалось обновить значения конфигова {name} Ошибка {err}")
    session.close()