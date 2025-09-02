from fastapi import APIRouter,Response
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from db_modules.db_query_config_start import (
    create_config_app_start_query
)

try:
    config_start_app=APIRouter(prefix="/config/app/start", tags=["Стартовая страница"])
    logger.debug("Инициализирован API стартовый")
except Exception as err:
    logger.error(f"Ошибка инициализации API: {err}")


class ConfigStartApp(BaseModel):
    app_port:int=7000
    sql_driver:str="sqlite"
    sql_host:Optional[str]=None
    sql_port:Optional[int]=None
    sql_db:str='ragi_db'
    sql_user:Optional[str]=None
    sql_password:Optional[str]=None
    db_path:Optional[str]='./instance'

@config_start_app.post("/create", summary="Создание установочных конфигов приложения")
async def start_configs_ai_api(
    configs_start_app: ConfigStartApp,
    response: Response,
):
    result = create_config_app_start_query(
        app_port=configs_start_app.app_port,
        sql_driver=configs_start_app.sql_driver,
        sql_host=configs_start_app.sql_host,
        sql_port=configs_start_app.sql_port,
        sql_db=configs_start_app.sql_db,
        sql_user=configs_start_app.sql_user,
        sql_password=configs_start_app.sql_password,
        db_path=configs_start_app.db_path
    )
    response.status_code = result["cod"]
    del result["cod"]
    return result