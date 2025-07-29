from flask_login import login_required, logout_user
from flask import render_template, redirect, url_for, request, flash
from flask.blueprints import Blueprint
from messanger.moduls import Auth
from loguru import logger

from db.db_query_auth import auth_query

try:
    logger.debug("Инициализация пути /auth")
    auth_app = Blueprint("auth", __name__, url_prefix="/auth")
except Exception as err:
    logger.error(f"Инициализация пути /auth не удалась Ошибка:{err}")


@auth_app.get("")
def auth_api():
    form = Auth()
    return render_template("auth.html", form=form)


@auth_app.post("/login")
def login_api():
    form = Auth()
    if form.send.data and form.validate_on_submit():
        try:
            login = form.login.data
            password = form.password.data
            remember = form.remember_auth.data
            logger.debug("Полученны поля формы авторизации")
        except Exception as err:
            logger.error(f"Не удалось получить поля формы авторизации Ошибка:{err}")
            flash(message="Не удалось прочитать форму", category="error")
            return redirect(request.referrer)
        auth_check = auth_query(login=login, password=password, remember=remember)
        if auth_check:
            return redirect(url_for("chats.chats_get_api"))
        else:
            return redirect(request.referrer)
    flash(message="Некорректные данные, авторизация не прошла", category="warning")
    return redirect(request.referrer)


@auth_app.get("/logout")
@login_required
def logout_api():
    logout_user()
    return redirect(url_for("index"))
