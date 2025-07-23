from sqlalchemy import select, update
from loguru import logger
from flask import flash

from db.db_create import Configs, db

def get_configs_ai():
    session = db.session
    try:
        search_config = session.execute(
            select(Configs.name, Configs.about, Configs.value).where(Configs.name.like('ai_%'))
        ).all()
        result = list()
        for config in search_config:
            result.append(
                {"name": config.name, "about": config.about, "value": config.value}
            )
        logger.trace(f"Получен список конфигов для AI из базы")
    except Exception as err:
        logger.error(f"Не удалось получить список конфигов для AI из базы Ошибка {err}")
    session.close

def get_configs():
    session = db.session
    try:
        search_config = session.execute(
            select(Configs.name, Configs.about, Configs.value).where(Configs.name.not_like('ai_%'))
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
        flash(message='Конфиг обнавлен',category='success')
    except Exception as err:
        logger.error(f"Не удалось обновить значения конфигова {name} Ошибка {err}")
        flash(message='Конфиг не обнавлен из за ошибки',category='error')
    session.close()