from flask_login import login_required, current_user
from flask import request, redirect, flash, render_template
from flask.blueprints import Blueprint
from loguru import logger

from db.db_query_config import get_configs_ai, update_config_ai
from db.db_query_users import get_user_role
from db.db_query_chat import get_chats

try:
    logger.debug("Инициализация пути /admin/ai/config")
    admin_ai_config_app = Blueprint(
        "admin_ai_config", __name__, url_prefix="/admin/ai/config"
    )
except Exception as err:
    logger.error(f"Инициализация пути /admin/ai/config не удалась Ошибка:{err}")


@admin_ai_config_app.get("")
@login_required
def ai_config_api():
    print(get_configs_ai())
    return render_template(
        "admin/config_ai.html",
        configs=get_configs_ai(),
        isAdmin=get_user_role(current_user.login),
        chats=get_chats(login=current_user.login),
    )


@admin_ai_config_app.post("/update")
@login_required
def ai_config_update_api():
    if get_user_role(current_user.login):
        try:
            name = request.form["config_name"]
            value = request.form["config_value"]
            logger.debug("Полученно из формы данных для обновления конфигов в базе")
        except Exception as err:
            logger.error(
                f"Не удалось получить данные из формы для обновления конфигов в базе Ошибка:{err}"
            )
        update_config_ai(name, value)
    else:
        flash(message="У вас нет прав на изменение", category="warning")
    return redirect(request.referrer)
