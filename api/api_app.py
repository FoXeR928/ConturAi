from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from loguru import logger


def init_pages():
    try:
        if os.path.exists("./instance/config.json") == True:
            from db_modules.db_query import check_config_ai
            from db_modules.db_query_config import get_config
            from api.api_auth import auth_app
            from api.api_config import config_app
            from api.api_chats import chat_app
            from api.api_users import users_app

            app.include_router(router=auth_app)
            app.include_router(router=config_app)
            app.include_router(router=chat_app)
            app.include_router(router=users_app)
            logger.debug("Инициализирован API")
            if check_config_ai() == True:
                try:
                    from api.api_ai import ai_app

                    app.include_router(router=ai_app)
                except Exception as err:
                    logger.error(f"Ошибка инициализации API AI: {err}")
            if bool(get_config(name="front_enable")) == True:
                from front.auth_pages import auth_pages_app
                from front.chats_pages import chats_pages_app
                from front.admin_pages import admin_pages_app

                app.mount(
                    "/static",
                    StaticFiles(directory="front/public/static"),
                    name="front",
                )
                app.include_router(router=auth_pages_app)
                app.include_router(router=chats_pages_app)
                app.include_router(router=admin_pages_app)
        else:
            from api.api_config_start import config_start_app
            from front.start_pages import start_pages_app

            app.mount(
                "/static", StaticFiles(directory="front/public/static"), name="front"
            )
            app.include_router(router=config_start_app)
            app.include_router(router=start_pages_app)

    except Exception as err:
        logger.error(f"Ошибка инициализации API: {err}")


if os.path.exists("./instance/config.json") == True:
    from db_modules.db_create_default import (
        create_default_users,
        create_default_config,
        create_default_config_ai,
    )

    create_default_config()
    create_default_config_ai()
    create_default_users()

try:
    app = FastAPI(
        title="Ragi_AI",
        description="Система для локального нейропомощника",
        version="1.14.2-alfa",
    )
except Exception as err:
    logger.critical(f"Ошибка инициализации приложения: {err}")
    exit()
init_pages()
