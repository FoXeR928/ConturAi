from sqlalchemy import update
import json
import os
from loguru import logger


def create_config_app_start_query(
    app_port: int,
    sql_driver: str,
    sql_host: str,
    sql_port: int,
    sql_db: str,
    sql_user: str,
    sql_password: str,
    db_path: str,
    front_enable: bool,
):
    try:
        data = {
            "sql_driver": sql_driver,
            "sql_host": sql_host,
            "sql_port": sql_port,
            "sql_db": sql_db,
            "sql_user": sql_user,
            "sql_password": sql_password,
            "db_path": db_path,
        }
        if os.path.exists("instance") == False:
            os.mkdir("instance")
        with open("instance/config.json", "w") as file_config:
            json.dump(data, file_config, indent=4)
        result = {
            "result": True,
            "message": "Стартовый конфиг приложения задан. Перезапустите сервер",
            "category": "success",
            "cod": 200,
        }
        from db_modules.db_create import Configs, session_create
        from db_modules.db_create_default import (
            create_default_users,
            create_default_config,
            create_default_config_ai,
        )

        create_default_users()
        create_default_config()
        create_default_config_ai()
        session = session_create
        session.execute(
            update(Configs).where(Configs.name == "app_port").values(value=app_port)
        )
        session.execute(
            update(Configs)
            .where(Configs.name == "front_enable")
            .values(value=front_enable)
        )
        session.commit()
        logger.success(f"Добавлены в базу конфиги для приложения")
    except Exception as err:
        logger.error(f"Не удалось задать стартовые конфиги приложения Ошибка {err}")
        result = {
            "result": False,
            "message": "Ошибка сервера стартовый конфиг приложения не задан",
            "category": "error",
            "cod": 500,
        }
    finally:
        session.close()
    return result
