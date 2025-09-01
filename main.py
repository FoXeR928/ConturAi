import uvicorn
from sys import stdout
from loguru import logger

from db_modules.db_query_config import get_config
from api.api_app import app

def init_log(log_level_file="INFO", log_level_std="WARNING"):
    try:
        logger.remove()
        logger.add(
            "logs/app.log",
            format="{time} | {level} | {message} | {name}",
            rotation="256 MB",
            retention=f"10 days",
            level=log_level_file,
        )
        if bool(int(get_config(name='debug'))) == True:
            log_level_std = "TRACE"
        logger.add(stdout, level=log_level_std)
        logger.info("Инициализирован файл логирования")
    except Exception as err:
        logger.error(f"Ошибка инициализации конфигов базы данных: {err}")
        exit()

if __name__ == "__main__":
    try:
        init_log()
        logger.info(f"Сервер запущен на порту {int(get_config(name="app_port"))}")
        uvicorn.run(app=app, host="0.0.0.0", port=int(get_config(name="app_port")))
    except Exception as err:
        logger.error(f"Ошибка инициализации сервера: {err}")
    finally:
        logger.info(f"Cервер остановлен")
