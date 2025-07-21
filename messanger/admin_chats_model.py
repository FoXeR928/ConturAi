from flask_login import login_required, current_user
from flask import request, redirect, flash, render_template
from flask.blueprints import Blueprint
from loguru import logger

from messanger.moduls import (
    check_nav,
    Delet_chats_irrevocably,
)
from db.db_query_chat import ( 
    delet_chats_irrevocably,
    get_delet_chats_irrevocably,
)
from db.db_query_users import get_user_role

try:
    logger.debug("Инициализация пути /admin/chats")
    admin_chats_app = Blueprint("admin_chats", __name__, url_prefix="/admin/chats")
except Exception as err:
    logger.error(f"Инициализация пути /admin/chats не удалась Ошибка:{err}")


@admin_chats_app.get("")
@login_required
def admin_chats_api():
    form_del_irr = Delet_chats_irrevocably()
    return render_template(
        "admin/admin_chats.html",
        form_del_irr=form_del_irr,
        chats=get_delet_chats_irrevocably(),
        nav=check_nav(current_user.login),
    )

@admin_chats_app.post("/delet_chats_irrevocably")
@login_required
def admin_delet_chats_irrevocably_api():
    form_del = Delet_chats_irrevocably()
    try:
        if form_del.send_del_chats.data and get_user_role(login=current_user.login):
            delet_chats_irrevocably()
            logger.success("Выполнен API запрос на безвозвратное удаление чатов")
    except Exception as err:
        logger.error(
            f"Невыполнен API запрос на безвозвратное удаление чатов Ошибка:{err}"
        )
    return redirect(request.referrer)
