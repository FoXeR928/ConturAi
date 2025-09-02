from fastapi import APIRouter,Request
from fastapi.templating import Jinja2Templates
from loguru import logger

templates = Jinja2Templates(directory="front/public/templates/")

try:
    chats_pages_app=APIRouter(prefix="/chats", tags=["Чаты веб-интерфейс"])
    logger.debug("Инициализирован API чаты")
except Exception as err:
    logger.error(f"Ошибка инициализации API: {err}")


@chats_pages_app.get("/", summary="Чаты")
async def chats_page(request: Request):
    return templates.TemplateResponse(name="chats/chats.html",context={'request': request})