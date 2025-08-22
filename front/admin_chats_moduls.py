from flask_login import login_required, current_user
from flask import request, redirect, render_template
from flask.blueprints import Blueprint
from loguru import logger

from db.db_query_chat import (
    delet_chats_irrevocably,
    delet_chats_irrevocably_checked,
    get_delet_chats_irrevocably,
    recovery_chats_checked,
)
from db.db_query_users import get_user_role
from db.db_query_chat import get_chats

try:
    logger.debug("Инициализация пути /admin/chats")
    admin_chats_app = Blueprint("admin_chats", __name__, url_prefix="/admin/chats")
except Exception as err:
    logger.error(f"Инициализация пути /admin/chats не удалась Ошибка:{err}")


@admin_chats_app.get("")
@login_required
def admin_chats_api():
    return render_template(
        "admin/admin_chats.html",
        chats_del=get_delet_chats_irrevocably(),
        isAdmin=get_user_role(login=current_user.login),
        chats=get_chats(login=current_user.login),
    )


@admin_chats_app.post("/delet")
@login_required
def admin_delet_chats_irrevocably_checked_api():
    if get_user_role(login=current_user.login):
        try:
            chats = request.form.getlist("chats[]")
            delet_chats_irrevocably_checked(chats=chats)
        except Exception as err:
            logger.error(f"Ошибка {err}")
    return redirect(request.referrer)


@admin_chats_app.get("/delet_chats_irrevocably")
@login_required
def admin_delet_chats_irrevocably_api():
    if get_user_role(login=current_user.login):
        delet_chats_irrevocably()
    return redirect(request.referrer)


@admin_chats_app.post("/recovery")
@login_required
def admin_recovery_chats_checked_api():
    if get_user_role(login=current_user.login):
        try:
            chats = request.form.getlist("chats[]")
            recovery_chats_checked(chats=chats)
        except Exception as err:
            logger.error(f"Ошибка {err}")
    return redirect(request.referrer)
