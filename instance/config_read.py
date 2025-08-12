import os
import json

from loguru import logger

if not os.path.exists("./instance/config.json"):
    data = {
        "CREATE_CONFIG": True,
        "CREATE_AI": True,
        "PORT": 7000,
        "DEBUG": False,
    }
    with open("./instance/config.json", "w") as file_config:
        json.dump(data, file_config, indent=4)
    logger.debug("Добавлен файл конфигов")

with open('./instance/config.json') as c:
    config=json.load(c)