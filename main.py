import uvicorn
from loguru import logger

from instance.config_read import init_confg
from api.api_app import app

config = init_confg()

if __name__ == "__main__":
    try:
        logger.info(f"Сервер запущен на порту {config['PORT']}")
        uvicorn.run(app=app, host="0.0.0.0", port=config["PORT"])
    except Exception as err:
        logger.error(f"Ошибка инициализации сервера: {err}")
    finally:
        logger.info(f"Cервер остановлен")
