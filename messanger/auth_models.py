from flask_login import login_required, logout_user, login_user
from flask import render_template, redirect, url_for, request,flash
from flask.blueprints import Blueprint
from messanger.moduls import Auth
from loguru import logger

from db.db_create import Users, db


try:
    logger.debug("Инициализация пути /auth")
    auth_app = Blueprint("auth", __name__, url_prefix="/auth")
except Exception as err:
    logger.error(f"Инициализация пути /auth не удалась Ошибка:{err}")


@auth_app.route("/login", methods=["GET", "POST"])
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
            flash(message='Не удалось прочитать форму',category='error')
        try:
            login_base = db.session.query(Users).filter(Users.login == login).one()
            logger.debug("Запрос в базу для проверки наличия пользователя")
        except Exception as err:
            logger.error(f"Не удалось проверить наличие пользователя Ошибка:{err}")
        if login_base.check_password(password):
            login_user(login_base, remember=remember)
            flash(message='Авторизация прошла успешно', category='success')
            return redirect(url_for("user.user_get_create_chats_api"))
        flash(message='Неверный логин или пароль', category='warning')
        return redirect(request.referrer)
    return render_template("auth.html", form=form)


@auth_app.get("/logout")
@login_required
def logout_api():
    logout_user()
    return redirect(url_for("auth.login_api"))
