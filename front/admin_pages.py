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
async def admin_page(request: Request):
    return templates.TemplateResponse(
        name="admin/admin.html", context={"request": request}
    )

@admin_pages_app.get("/chats", summary="Администрирование чатов")
async def chats_page(request: Request):
    return templates.TemplateResponse(
        name="admin/chats.html", context={"request": request}
    )

@admin_pages_app.get("/users", summary="Администрирование пользователей")
async def users_page(request: Request):
    return templates.TemplateResponse(
        name="admin/users.html", context={"request": request}
    )

@admin_pages_app.get("/docs", summary="Администрирование документов")
async def docs_page(request: Request):
    return templates.TemplateResponse(
        name="admin/docs.html", context={"request": request}
    )

@admin_pages_app.get("/configs", summary="Администрирование конфигурации")
async def configs_page(request: Request):
    return templates.TemplateResponse(
        name="admin/configs.html", context={"request": request}
    )

@admin_pages_app.get("/configs_ai", summary="Администрирование конфигурации AI")
async def configs_ai_page(request: Request):
    return templates.TemplateResponse(
        name="admin/configs_ai.html", context={"request": request}
    )