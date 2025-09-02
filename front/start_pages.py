from fastapi import APIRouter,Request
from fastapi.templating import Jinja2Templates
from loguru import logger

templates = Jinja2Templates(directory="front/public/templates/")

try:
    start_pages_app=APIRouter(prefix="", tags=["Стартовая страница веб-интерфейс"])
    logger.debug("Инициализирован API стартовый")
except Exception as err:
    logger.error(f"Ошибка инициализации API: {err}")


@start_pages_app.get("/", summary="Создание установочных конфигов приложения")
async def start_configs_ai_page(request: Request):
    return templates.TemplateResponse(name="start_config/start_config.html",context={'request': request})