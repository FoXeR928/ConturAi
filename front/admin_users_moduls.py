from flask_login import login_required, current_user
from flask import request, redirect, flash, render_template
from flask.blueprints import Blueprint
from loguru import logger

from front.moduls import Create_user, Update_password
from db.db_query_users import add_user_status, get_users, reg_user, delet_user
from db.db_query_users import get_user_role, update_password_user
from db.db_query_chat import get_chats

try:
    logger.debug("Инициализация пути /admin/users")
    admin_users_app = Blueprint("admin_users", __name__, url_prefix="/admin/users")
except Exception as err:
    logger.error(f"Инициализация пути /admin/users не удалась Ошибка:{err}")


@admin_users_app.get("")
@login_required
def admin_users_api():
    form_user = Create_user()
    form_password = Update_password()
    return render_template(
        "admin/users.html",
        admin=current_user.login,
        form_user=form_user,
        form_password=form_password,
        users=get_users(),
        isAdmin=get_user_role(current_user.login),
        chats=get_chats(login=current_user.login),
    )


@admin_users_app.post("/add_user")
def admin_user_add_api():
    form_user = Create_user()
    if (
        form_user.send_reg.data
        and form_user.validate_on_submit()
        and get_user_role(current_user.login)
    ):
        try:
            login = form_user.login_reg.data
            user_name = form_user.user_name_reg.data
            password = form_user.password_reg.data
            logger.debug("Полученно из формы данных пользователя для регистрации")
        except Exception as err:
            logger.error(
                f"Не удалось получить данные из формы для регистрации пользователя Ошибка:{err}"
            )
        reg_user(login, password, user_name)
    else:
        flash(message="Не корректное заполнение полей", category="warning")
    return redirect(request.referrer)


@admin_users_app.post("/update_user")
def admin_user_update_api():
    form_password = Update_password()
    if form_password.send_update.data and get_user_role(current_user.login):
        try:
            login = form_password.login_update.data
            password = form_password.password_update.data
            role = form_password.role_update.data
            logger.debug(
                "Полученно из формы данных пользователя для обновления информации пользователя"
            )
        except Exception as err:
            logger.error(
                f"Не удалось получить данные из формы для смены пароля пользователя админом Ошибка:{err}"
            )
            flash(
                message="Не удалось получить значения на изменение", category="warning"
            )
            redirect(request.referrer)
        if password != "" and role != "None":
            try:
                update_password_user(
                    login=login,
                    password=password,
                    user_update_password=current_user.login,
                )
                add_user_status(login=login, role=role)
                logger.trace(
                    f"Выполнен API запрос на смену пароля и роли пользователя {login}"
                )
                flash(message="Пароль и роль изменены", category="success")
            except Exception as err:
                logger.error(
                    f"Невыполнен API запрос на смену пароля и роли пользователя {login} статуса Ошибка: {err}"
                )
                flash(
                    message=f"Невыполнен API запрос на смену пароля и роли пользователя {login} статуса Ошибка: {err}",
                    category="error",
                )
        elif password != "":
            try:
                update_password_user(
                    login=login,
                    password=password,
                    user_update_password=current_user.login,
                )
                logger.trace(
                    f"Выполнен API запрос на смену пароля пользователя {login}"
                )
                flash(message="Пароль изменен", category="success")
            except Exception as err:
                logger.error(
                    f"Невыполнен API запрос на смену пароля пользователя {login} статуса Ошибка: {err}"
                )
                flash(
                    message=f"Невыполнен API запрос на смену пароля пользователя {login} статуса Ошибка: {err}",
                    category="error",
                )
        elif role != "None":
            try:
                add_user_status(login=login, role=role)
                logger.debug(f"Выполнен API запрос на смену роли пользователя {login}")
            except Exception as err:
                logger.error(
                    f"Невыполнен API запрос на смену роли пользователя {login} Ошибка:{err}"
                )
    else:
        flash(message="Нет прав на изменение", category="warning")
    return redirect(request.referrer)


@admin_users_app.get("/delet_user/<login>")
def admin_user_delet_api(login: str):
    if get_user_role(current_user.login):
        try:
            logger.trace(
                "Полученно из формы данных пользователя для удаления пользователя"
            )
        except Exception as err:
            logger.error(
                f"Не удалось получить данные из формы для смены пароля пользователя админом Ошибка:{err}"
            )
            flash(
                message="Не удалось получить значения на изменение", category="warning"
            )
        delet_user(login=login)
    else:
        flash(message="Нет прав на удаление пользователя", category="warning")
    return redirect(request.referrer)
