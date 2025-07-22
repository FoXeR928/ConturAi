from flask_login import login_required, current_user
from flask import request, redirect, flash, render_template
from flask.blueprints import Blueprint
from loguru import logger

from messanger.moduls import (
    check_nav,
    Config_update,
)
from db.db_query_config import ( 
    update_config,
    get_configs,
)
from db.db_query_users import get_user_role

try:
    logger.debug("Инициализация пути /admin/config")
    admin_app = Blueprint("admin_config", __name__, url_prefix="/admin/config")
except Exception as err:
    logger.error(f"Инициализация пути /admin/config не удалась Ошибка:{err}")

@admin_app.get("")
@login_required
def admin_config_api():
    form = Config_update()
    if (form.config_value.data
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
        redirect(request.referrer)
    return render_template(
        "admin/config.html",
        form=form,
        configs=get_configs(),
        nav=check_nav(current_user.login),
    )

@admin_app.get("/update")
@login_required
def admin_config_update_api():
    form = Config_update()
    if (form.config_value.data
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
        flash(message='')
    return redirect(request.referrer)