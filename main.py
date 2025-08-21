from fastapi import FastAPI
import uvicorn
from loguru import logger
from sys import stdout

from instance.config_read import init_confg
from db_modules.db_create_default import create_default_users,create_default_config,create_default_config_ai

def init_log(log_level_file="INFO", log_level_std="WARNING"):
    logger.remove()
    logger.add(
        "logs/app.log",
        format="{time} | {level} | {message} | {name}",
        rotation="256 MB",
        retention=f"10 days",
        level=log_level_file,
    )
    if config['DEBUG']==True:
        log_level_std = "TRACE"
    logger.add(stdout, level=log_level_std)

def init_pages():
    try:
        from api.api_auth import auth_app
        from api.api_config import config_app
        from api.api_chat import chat_app

        app.include_router(router=auth_app)
        app.include_router(router=config_app)
        app.include_router(router=chat_app)
        logger.debug('Инициализирован API')
    except Exception as err:
        logger.error(f'Ошибка инициализации API: {err}')

def init_ai():
    try:
        from api.api_ai import ai_app

        app.include_router(router=ai_app)
    except Exception as err:
        logger.error(f'Ошибка инициализации API AI: {err}')

config=init_confg()

init_log()

app=FastAPI()

create_default_config()
create_default_config_ai()
create_default_users()

init_pages()
if config["CREATE_AI"]==True:
    init_ai()

if __name__=='__main__':
    try:
        logger.info(f'Сервер запущен на порту {config['PORT']}')
        uvicorn.run(app=app,host='0.0.0.0',port=config['PORT'])
    except Exception as err:
        logger.error(f'Ошибка инициализации сервера: {err}')
    finally:
        logger.info(f'Cервер остановлен')