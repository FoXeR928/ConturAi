from flask_login import login_required, current_user
from flask import request, redirect, flash, render_template
from flask.blueprints import Blueprint
from loguru import logger

from messanger.moduls import (
    Config_update,
)
from db.db_query_config import ( 
    update_config,
    get_configs,
)
from db.db_query_users import get_user_role
from db.db_query_chat import get_chats

try:
    logger.debug("Инициализация пути /admin")
    admin_app = Blueprint("admin", __name__, url_prefix="/admin")
except Exception as err:
    logger.error(f"Инициализация пути /admin не удалась Ошибка:{err}")

@admin_app.get("")
@login_required
def admin_api():
    form = Config_update()
    return render_template(
        "admin/config.html",
        form=form,
        configs=get_configs(),
        isAdmin=get_user_role(current_user.login),
        chats=get_chats(login=current_user.login)
    )