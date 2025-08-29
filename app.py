from fastapi import FastAPI
from sys import stdout
from loguru import logger

from db_modules.db_create import init_db
from instance.config_read import init_confg
from db_modules.db_create_default import (
    create_default_users,
    create_default_config,
    create_default_config_ai,
)
from db_modules.db_query import check_config_ai


def init_log(log_level_file="INFO", log_level_std="WARNING"):
    logger.remove()
    logger.add(
        "logs/app.log",
        format="{time} | {level} | {message} | {name}",
        rotation="256 MB",
        retention=f"10 days",
        level=log_level_file,
    )
    if config["DEBUG"] == True:
        log_level_std = "TRACE"
    logger.add(stdout, level=log_level_std)


def init_pages():
    try:
        from api.api_auth import auth_app
        from api.api_config import config_app
        from api.api_chat import chat_app
        from api.api_users import users_app

        app.include_router(router=auth_app)
        app.include_router(router=config_app)
        app.include_router(router=chat_app)
        app.include_router(router=users_app)
        logger.debug("Инициализирован API")
    except Exception as err:
        logger.error(f"Ошибка инициализации API: {err}")


def init_ai():
    try:
        from api.api_ai import ai_app

        app.include_router(router=ai_app)
    except Exception as err:
        logger.error(f"Ошибка инициализации API AI: {err}")


def init_app():
    try:
        app = FastAPI(
            title="Ragi_AI",
            description="Система для локального нейропомощника",
            version="1.10.0.2",
        )
        return app
    except Exception as err:
        logger.critical(f"Ошибка инициализации приложения: {err}")
        exit()


config = init_confg()
init_log()
engine = init_db()
create_default_config()
create_default_config_ai()
create_default_users()
app = init_app()
init_pages()
if check_config_ai() == True:
    init_ai()
