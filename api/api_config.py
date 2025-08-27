from fastapi import APIRouter, Response, Depends
from pydantic import BaseModel
from typing import Any
from loguru import logger

from api.api_auth import User, get_current_user
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
async def get_configs_ai_api(
    response: Response, current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = get_configs_ai_query()
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 403,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@config_app.get("/app", summary="Получение конфигов приложения")
async def get_configs_app_api(
    response: Response, current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = get_configs_query()
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 403,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@config_app.patch("/ai/update", summary="Обновление конфига AI")
async def update_config_ai_api(
    config_data: ConfigUpdate,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        result = update_config_ai_query(name=config_data.name, value=config_data.value)
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 403,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@config_app.patch("/app/update", summary="Обновление конфига приложения")
async def update_config_app_api(
    config_data: ConfigUpdate,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        result = update_config_query(name=config_data.name, value=config_data.value)
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 403,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@config_app.post("/ai/start", summary="Создание установочных конфигов AI")
async def start_configs_ai_api(
    configs_data: ConfigStart,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        result = create_config_ai_start(configs=configs_data)
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 403,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result
