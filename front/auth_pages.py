from fastapi import APIRouter,Request
from fastapi.templating import Jinja2Templates
from loguru import logger

templates = Jinja2Templates(directory="front/public/templates/")

try:
    auth_pages_app=APIRouter(prefix="", tags=["Авторизация веб-интерфейс"])
    logger.debug("Инициализирован API авторизации")
except Exception as err:
    logger.error(f"Ошибка инициализации API: {err}")


@auth_pages_app.get("/", summary="Авторизация")
async def auth_page(request: Request):
    return templates.TemplateResponse(name="auth/auth.html",context={'request': request})