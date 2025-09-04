from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from loguru import logger

templates = Jinja2Templates(directory="front/public/templates/")

try:
    admin_pages_app = APIRouter(
        prefix="/admin", tags=["Администрирование веб-интерфейс"]
    )
    logger.debug("Инициализирован API чаты")
except Exception as err:
    logger.error(f"Ошибка инициализации API: {err}")


@admin_pages_app.get("/", summary="Администрирование")
async def chats_page(request: Request):
    return templates.TemplateResponse(
        name="admin/admin.html", context={"request": request}
    )
