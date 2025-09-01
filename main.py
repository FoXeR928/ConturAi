import uvicorn
from sys import stdout
import os
from loguru import logger

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

if os.path.exists("./instance/config.json")==True:
    from db_modules.db_query_config import get_config

    init_log()
    app="api.api_app:app"
    port=int(get_config(name="app_port"))
else:
    app="api.api_config_start:app"
    port=7000

if __name__ == "__main__":
    try:
        logger.info(f"Сервер запущен на порту {port}")
        uvicorn.run(app=app, host="0.0.0.0", port=port)
    except Exception as err:
        logger.error(f"Ошибка инициализации сервера: {err}")
    finally:
        logger.info(f"Cервер остановлен")
