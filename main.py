from sys import stdout
import os
from time import sleep
import uvicorn
from multiprocessing import Process
from loguru import logger
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
        if bool(int(get_config(name="debug"))) == True:
            log_level_std = "TRACE"
        logger.add(stdout, level=log_level_std)
        logger.info("Инициализирован файл логирования")
    except Exception as err:
        logger.error(f"Ошибка инициализации конфигов базы данных: {err}")
        exit()


if os.path.exists("./instance/config.json") == True:
    from db_modules.db_query_config import get_config

    port = int(get_config(name="app_port"))
    init_log()
else:
    port = 7000


class ServerManager:
    def __init__(self):
        self.proccess: Process = None

    def start_server(self):
        def run_server():
            try:
                uvicorn.run(app=app, host="0.0.0.0", port=port)
                logger.info(f"Сервер запущен на порту {port}")
            except Exception as err:
                logger.critical(f"Ошибка запустить сервера: {err}")
                exit()

        try:
            self.proccess = Process(target=run_server, daemon=True)
            self.proccess.start()
            logger.info(f"Сервер запущен на порту {port}")
        except Exception as err:
            logger.critical(f"Ошибка запустить сервера: {err}")

    def reload_server(self):
        if self.proccess == True:
            self.proccess.terminate()
        sleep(5)
        return self.start_server()

    def stop_server(self):
        if self.proccess == True:
            self.proccess.terminate()
        logger.info("Сервер остановлен")


manager = ServerManager()

if __name__ == "__main__":
    # manager.start_server
    try:
        uvicorn.run(app=app, host="0.0.0.0", port=port)
        logger.info(f"Сервер запущен на порту {port}")
    except Exception as err:
        logger.critical(f"Ошибка запустить сервера: {err}")
        exit()
