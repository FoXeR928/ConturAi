from sqlalchemy import select, update
import json
import os
from loguru import logger

from db_modules.db_create import Configs, Configs_ai, session_create

def check_config(name: str):
    session = session_create
    try:
        config = session.scalars(select(Configs).where(Configs.name == name)).one_or_none()
        logger.trace(f"Проверка чата {name} в базе")
        if config != None:
            result = True
        else:
            result = False
        logger.debug(f"Проверка чата {name} в базе прошла успешно")
    except Exception as err:
        logger.error(f"Не удалось проверить чата {name} Ошибка {err}")
        result = False
    finally:
        session.close()
    return result

def check_config_ai(name: str):
    session = session_create
    try:
        config = session.scalars(select(Configs_ai).where(Configs_ai.name == name)).one_or_none()
        logger.trace(f"Проверка чата {name} в базе")
        if config != None:
            result = True
        else:
            result = False
        logger.debug(f"Проверка чата {name} в базе прошла успешно")
    except Exception as err:
        logger.error(f"Не удалось проверить чата {name} Ошибка {err}")
        result = False
    finally:
        session.close()
    return result

def get_config_ai(name: str):
    session = session_create
    try:
        search_config = session.scalars(
            select(Configs_ai.value).where(Configs_ai.name == name)
        ).first()
        result = search_config
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
    session = session_create
    try:
        search_config = session.scalars(
            select(Configs.value).where(Configs.name == name)
        ).first()
        result = search_config
        logger.trace(f"Получено значения конфигова {name} из базы")
    except Exception as err:
        logger.error(
            f"Не удалось получить значения конфигова {name} из базы Ошибка {err}"
        )
        result = None
    finally:
        session.close()
    return result

def get_configs_ai_query():
    session = session_create
    try:
        search_config = session.execute(
            select(
                Configs_ai.name,
                Configs_ai.about,
                Configs_ai.value,
                Configs_ai.input_format,
            )
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
        result = {
            "result": True,
            "configs_ai": search_result,
            "message": "Конфиги получены",
            "category": "success",
            "cod": 200,
        }
        logger.trace(f"Получен список конфигов для AI из базы")
    except Exception as err:
        logger.error(f"Не удалось получить список конфигов для AI из базы Ошибка {err}")
        return {
            "result": False,
            "message": "Ошибка сервера не удалось получить конфиги AI",
            "category": "error",
            "cod": 500,
        }
    finally:
        session.close()
    return result

def update_config_ai_query(name: str, value):
    if check_config_ai(name=name)==True:
        session = session_create
        try:
            session.execute(
                update(Configs_ai).where(Configs_ai.name == name).values(value=value)
            )
            session.commit()
            logger.success(f"Обноваление значения конфигова {name} на {value} из базы")
            result = {
                "result": True,
                "message": "Конфиг обнавлен",
                "category": "success",
                "cod": 200,
            }
        except Exception as err:
            logger.error(f"Не удалось обновить значения конфигова {name} Ошибка {err}")
            result = {
                "result": False,
                "message": "Ошибка сервера конфиг не обнавлен",
                "category": "error",
                "cod": 500,
            }
        finally:
            session.close()
    else:
        result = {
            "result": False,
            "message": "Не найден конфиг",
            "category": "warning",
            "cod": 404,
        }
    return result

def create_config_ai_start_query(
    model_chunk: str,
    model: str,
    collection: str = "ragi_db",
    rag_host: str = "localhost",
    rag_port_http: int = 6333,
    rag_port_grpc: int = 6333,
    rag_grpc: bool = False,
):
    configs_list = (
        ("model_chunk", "Модель для генерации чанков", model_chunk, "text"),
        ("model", "Модель для генерации ответа", model, "text"),
        ("collection", "Название векторной коллекции", collection, "text"),
        ("rag_host", "Хост Qdrant", rag_host, "text"),
        ("rag_port_http", "HTTP порт Qdrant", rag_port_http, "number"),
        ("rag_port_grpc", "GRPC порт Qdrant", rag_port_grpc, "number"),
        ("rag_grpc", "Использовать GRPC порт Qdrant", rag_grpc, "boolen"),
    )
    session = session_create
    try:
        for configs in configs_list:
            check_conf = session.scalars(
                select(Configs_ai).where(Configs_ai.name == configs[0])
            ).one_or_none()
            if check_conf == None:
                config = Configs_ai(
                    name=configs[0],
                    about=configs[1],
                    value=configs[2],
                    input_format=configs[3],
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
        result = {
            "result": True,
            "message": "Стартовый конфиг AI задан",
            "category": "success",
            "cod": 200,
        }
    except Exception as err:
        logger.error(f"Не удалось задать стартовые конфиги AI Ошибка {err}")
        result = {
            "result": False,
            "message": "Ошибка сервера стартовый конфиг AI не задан",
            "category": "error",
            "cod": 500,
        }
    finally:
        session.close()
    return result

def get_configs_query():
    session = session_create
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
        result = {
            "result": True,
            "configs_ai": search_result,
            "message": "Конфиги получены",
            "category": "success",
            "cod": 200,
        }
        logger.trace(f"Получен список конфигов из базы")
    except Exception as err:
        logger.error(f"Не удалось получить список конфигов из базы Ошибка {err}")
        return {
            "result": False,
            "message": "Ошибка сервера не удалось получить конфиги приложения",
            "category": "error",
            "cod": 500,
        }
    finally:
        session.close()
    return result

def update_config_query(name: str, value):
    if check_config(name=name)==True:
        session = session_create
        try:
            session.execute(update(Configs).where(Configs.name == name).values(value=value))
            session.commit()
            logger.success(f"Обноваление значения конфигова {name} на {value} из базы")
            result = {
                "result": True,
                "message": "Конфиг обнавлен",
                "category": "success",
                "cod": 200,
            }
        except Exception as err:
            logger.error(f"Не удалось обновить значения конфигова {name} Ошибка {err}")
            result = {
                "result": False,
                "message": "Ошибка сервера конфиг не обнавлен",
                "category": "error",
                "cod": 500,
            }
        finally:
            session.close()
    else:
        result = {
            "result": False,
            "message": "Не найден конфиг",
            "category": "warning",
            "cod": 404,
        }
    return result