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
    logger.debug("Инициализация пути /admin/config")
    admin_config_app = Blueprint("admin_config", __name__, url_prefix="/admin/config")
except Exception as err:
    logger.error(f"Инициализация пути /admin/config не удалась Ошибка:{err}")


@admin_config_app.get("")
@login_required
def admin_config_api():
    form = Config_update()
    return render_template(
        "admin/config.html",
        form=form,
        configs=get_configs(),
        isAdmin=get_user_role(current_user.login),
        chats=get_chats(login=current_user.login),
    )


@admin_config_app.get("/update")
@login_required
def admin_config_update_api():
    form = Config_update()
    if (
        form.config_value.data
        and form.validate_on_submit()
        and get_user_role(current_user.login)
    ):
        try:
            name = form.config_name.data
            value = form.config_value.data
            logger.debug("Полученно из формы данных для обновления конфигов в базе")
        except Exception as err:
            logger.error(
                f"Не удалось получить данные из формы для обновления конфигов в базе Ошибка:{err}"
            )
        update_config(name, value)
    else:
        flash(message="Не удалось проверить прочитать знычения", category="warning")
    return redirect(request.referrer)
