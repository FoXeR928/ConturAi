from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Any
from loguru import logger

from api.api_auth import UserToken
from db_modules.db_query import admin_auth_check
from db_modules.db_query_config import (
    get_configs_ai_query,
    get_configs_query,
    update_config_ai_query,
    update_config_query,
    create_config_ai_start,
)

try:
    config_app = APIRouter(prefix="/configs", tags=["Конфиги"])
    logger.debug("Инициализирован API конфигов")
except Exception as err:
    logger.error(f"Ошибка инициализации API: {err}")


class ConfigUpdate(BaseModel):
    name: str
    value: Any


class ConfigStart(BaseModel):
    model_chunk: str
    model: str
    collection: str = "ragi_db"
    rag_host: str = "localhost"
    rag_port_http: int = 6333
    rag_port_grpc: int = 6334
    rag_grpc: bool = False


@config_app.get("/ai", summary="Получение конфигов AI")
async def get_configs_ai_api(token_data: UserToken, response: Response):
    auth = admin_auth_check(login=token_data.login, token=token_data.user_token)
    if auth == True:
        result = get_configs_ai_query()
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 401,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@config_app.get("/app", summary="Получение конфигов приложения")
async def get_configs_ai_api(token_data: UserToken, response: Response):
    auth = admin_auth_check(login=token_data.login, token=token_data.user_token)
    if auth == True:
        result = get_configs_query()
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 401,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@config_app.patch("/ai/update", summary="Обновление конфига AI")
async def get_configs_ai_api(
    token_data: UserToken, config_data: ConfigUpdate, response: Response
):
    auth = admin_auth_check(login=token_data.login, token=token_data.user_token)
    if auth == True:
        result = update_config_ai_query(name=config_data.name, value=config_data.value)
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 401,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@config_app.patch("/app/update", summary="Обновление конфига приложения")
async def get_configs_ai_api(
    token_data: UserToken, config_data: ConfigUpdate, response: Response
):
    auth = admin_auth_check(login=token_data.login, token=token_data.user_token)
    if auth == True:
        result = update_config_query(name=config_data.name, value=config_data.value)
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 401,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@config_app.post("/ai/start", summary="Создание установочных конфигов AI")
async def start_configs_ai_api(
    token_data: UserToken, configs_data: ConfigStart, response: Response
):
    auth = admin_auth_check(login=token_data.login, token=token_data.user_token)
    if auth == True:
        result = create_config_ai_start(configs=configs_data)
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 401,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result
