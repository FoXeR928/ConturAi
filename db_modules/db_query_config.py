from sqlalchemy import select, update
from loguru import logger

from db_modules.db_create import Configs, Configs_ai, session_create


def get_configs_ai_query():
    session = session_create()
    try:
        search_config = session.execute(
            select(
            Configs_ai.name,
            Configs_ai.about,
            Configs_ai.value,
            Configs_ai.input_format,
        )).all()
        search_result = list()
        for config in search_config:
            search_result.append(
                {
                    "name": config.name,
                    "about": config.about,
                    "value": config.value,
                    "input_format": config.input_format,
                }
            )
        result={'result':True,'configs_ai':search_result,'message':"Конфиги получены", 'category':"success",'cod':200}
        logger.trace(f"Получен список конфигов для AI из базы")
    except Exception as err:
        logger.error(f"Не удалось получить список конфигов для AI из базы Ошибка {err}")
        return {'result':False,'message':"Ошибка сервера не удалось получить конфиги AI", 'category':"error",'cod':500}
    finally:
        session.close()
    return result

def get_configs_query():
    session = session_create()
    try:
        search_config = session.execute(
            select(Configs.name, Configs.about, Configs.value, Configs.input_format)
        ).all()
        search_result = list()
        for config in search_config:
            search_result.append(
                {
                    "name": config.name,
                    "about": config.about,
                    "value": config.value,
                    "input_format": config.input_format,
                }
            )
        result={'result':True,'configs_ai':search_result,'message':"Конфиги получены", 'category':"success",'cod':200}
        logger.trace(f"Получен список конфигов из базы")
    except Exception as err:
        logger.error(f"Не удалось получить список конфигов из базы Ошибка {err}")
        return {'result':False,'message':"Ошибка сервера не удалось получить конфиги приложения", 'category':"error",'cod':500}
    finally:
        session.close()
    return result

def update_config_ai_query(name: str, value):
    session = session_create()
    try:
        session.execute(
            update(Configs_ai).where(Configs_ai.name == name).values(value=value)
        )
        session.commit()
        logger.success(f"Обноваление значения конфигова {name} на {value} из базы")
        result={'result':True,'message':"Конфиг обнавлен", 'category':"success",'cod':200}
    except Exception as err:
        logger.error(f"Не удалось обновить значения конфигова {name} Ошибка {err}")
        result={'result':False,'message':"Ошибка сервера конфиг не обнавлен", 'category':"error",'cod':500}
    finally:
        session.close()
    return result

def update_config_query(name: str, value):
    session = session_create()
    try:
        session.execute(update(Configs).where(Configs.name == name).values(value=value))
        session.commit()
        logger.success(f"Обноваление значения конфигова {name} на {value} из базы")
        result={'result':True,'message':"Конфиг обнавлен", 'category':"success",'cod':200}
    except Exception as err:
        logger.error(f"Не удалось обновить значения конфигова {name} Ошибка {err}")
        result={'result':False,'message':"Ошибка сервера конфиг не обнавлен", 'category':"error",'cod':500}
    finally:
        session.close()
    return result

def get_config_ai(name: str):
    session = session_create()
    try:
        search_config = session.execute(
            select(Configs_ai.value).where(Configs_ai.name == name)
        ).first()
        result = search_config.value
        logger.trace(f"Получено значения конфигова {name} из базы")
    except Exception as err:
        logger.error(
            f"Не удалось получить значения конфигова {name} из базы Ошибка {err}"
        )
        result = None
    finally:
        session.close()
    return result

def get_config(name: str):
    session = session_create()
    try:
        search_config = session.execute(
            select(Configs.value).where(Configs.name == name)
        ).first()
        result = search_config.value
        logger.trace(f"Получено значения конфигова {name} из базы")
    except Exception as err:
        logger.error(
            f"Не удалось получить значения конфигова {name} из базы Ошибка {err}"
        )
        result = None
    finally:
        session.close()
    return result

def create_config_ai_start(configs):
    session = db.session
    try:
        for config in configs:
            check_conf = session.scalars(
                select(Configs_ai).where(Configs_ai.name == config[0])
            ).one_or_none()
            if check_conf == None:
                config = Configs_ai(
                    name=config[0],
                    about=config[1],
                    value=config[2],
                    input_format=config[3],
                )
                session.add(config)
            else:
                session.execute(
                    update(Configs_ai)
                    .where(Configs_ai.name == config[0])
                    .values(value=config[2])
                )
            session.commit()
        logger.success(f"Добавлены в базу конфиги для AI")
        flash(message="Конфигии AI добавлены в базу", category="success")
    except Exception as err:
        flash(message="Не удалось добавлены в базу конфиги для AI", category="error")
        logger.error(f"Не удалось добавлены в базу конфиги для AI Ошибка {err}")
    session.close()






