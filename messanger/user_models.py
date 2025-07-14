from flask_login import login_required, current_user
from flask import render_template, request, redirect
from flask.blueprints import Blueprint
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SubmitField,
    HiddenField,
)
from wtforms.validators import DataRequired, Length
from loguru import logger

from db.db_query import (
    get_user_role,
    update_password_user,
)
from db.db_query_admin import get_users,reg_user, get_configs, update_config
from db.db_query_chat import get_chats, get_messages_chat, get_messages_ai, create_chat, create_message
from ai_chat.ask import ask_query
from ai_chat.query_rag_db import add_docs
from ai_chat.parther import normalize_text, chunk_create

try:
    logger.debug("Инициализация пути /users")
    user_app = Blueprint("user", __name__, url_prefix="/user")
except Exception as err:
    logger.error(f"Инициализация пути /users не удалась Ошибка:{err}")


class Create_chat(FlaskForm):
    chat = StringField("Название чата", validators=[DataRequired(), Length(min=1)])
    send_chat = SubmitField("Создать")


class Send_message(FlaskForm):
    message = StringField("Текст", validators=[DataRequired(), Length(min=1)])
    send_message = SubmitField("Отправить")


class Create_user(FlaskForm):
    login_reg = StringField("Логин", validators=[DataRequired(), Length(min=1)])
    user_name_reg = StringField("Имя", validators=[DataRequired(), Length(min=1)])
    password_reg = PasswordField("Пароль", validators=[DataRequired(), Length(min=8)])
    send_reg = SubmitField("Создать")


class Update_password(FlaskForm):
    login_update = HiddenField(
        "Пользоватль", validators=[DataRequired(), Length(min=1)]
    )
    password_update = PasswordField(
        "Пароль", validators=[DataRequired(), Length(min=8)]
    )
    send_update = SubmitField("Изменить")


class File_text(FlaskForm):
    file_name_text = StringField(
        "Имя файла", validators=[DataRequired(), Length(min=1)]
    )
    file_text = TextAreaField("Текст файла", validators=[DataRequired(), Length(min=1)])
    send_text = SubmitField("Загрузить")


class Config_update(FlaskForm):
    config_name = HiddenField("Имя конфига", validators=[DataRequired(), Length(min=1)])
    config_value = StringField(
        "Значение конфига", validators=[DataRequired(), Length(min=1)]
    )
    send_config = SubmitField("Сохранить")

class Config_update_textaria(FlaskForm):
    config_name = HiddenField("Имя конфига", validators=[DataRequired(), Length(min=1)])
    config_value = TextAreaField(
        "Значение конфига", validators=[DataRequired(), Length(min=1)]
    )
    send_config = SubmitField("Сохранить")


def check_nav(login):
    nav = {"user.user_get_create_chats_api": "Чаты"}
    if get_user_role(login):
        nav["user.admin_users_api"] = "Пользователи"
        nav["user.admin_docs_api"] = "Документы"
        nav["user.admin_config_api"] = "Конфигурации"
    nav["auth.logout_api"] = "Выйти"
    logger.trace("Генерация ссылок навигации")
    return nav


@user_app.route("/chats", methods=["GET", "POST"])
@login_required
def user_get_create_chats_api():
    nav = check_nav(current_user.login)
    chats = get_chats(current_user.login)
    form = Create_chat()
    if form.validate_on_submit():
        try:
            chat = form.chat.data
            logger.debug("Полученно имя чата из формы")
        except Exception as err:
            logger.error(f"Не удалось получить поле с именем чата Ошибка:{err}")
        create_chat(current_user.login, chat)
        return redirect(request.referrer)
    return render_template(
        "chats/user_chats.html",
        chats=chats,
        form=form,
        login=current_user.login,
        nav=nav,
    )


@user_app.route("/chats/<chat>", methods=["GET", "POST"])
@login_required
def user_get_chat_api(chat: str):
    messages = get_messages_chat(login=current_user.login,chat_id=chat)
    form = Send_message()
    if form.validate_on_submit():
        try:
            text = form.message.data
            logger.debug("Полученно сообщения из формы чата")
        except Exception as err:
            logger.error(f"Не удалось получить поле с сообщением чата Ошибка:{err}")
        messages_history = get_messages_ai(chat)
        if messages_history!=None:
            create_message(login=current_user.login,chat_id=chat, text=text)
            ask_query(query=text, chat_id=chat, messages_history=messages_history)
        return(request.referrer)
    return render_template(
        "chats/chat.html",
        messages=messages["messages"],
        form=form,
        chat_name=messages["name"],
        chat_id=chat,
        login=current_user.login,
    )


@user_app.route("/admin/users", methods=["GET", "POST"])
@login_required
def admin_users_api():
    nav = check_nav(current_user.login)
    form_user = Create_user()
    form_password = Update_password()
    users = get_users()
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
        return redirect(request.referrer)
    if (
        form_password.send_update.data
        and form_password.validate_on_submit()
        and get_user_role(current_user.login)
    ):
        try:
            login = form_password.login_update.data
            password = form_password.password_update.data
            logger.debug(
                "Полученно из формы данных пользователя для смены пароля админом"
            )
        except Exception as err:
            logger.error(
                f"Не удалось получить данные из формы для смены пароля пользователя админом Ошибка:{err}"
            )
        update_password_user(current_user.login, login, password)
        return redirect(request.referrer)
    return render_template(
        "admin/users.html",
        admin=current_user.login,
        form_user=form_user,
        form_password=form_password,
        users=users,
        nav=nav,
    )


@user_app.route("/admin/docs", methods=["GET", "POST"])
@login_required
def admin_docs_api():
    nav = check_nav(current_user.login)
    form_file = File_text()
    if (
        form_file.send_text.data
        and form_file.validate_on_submit()
        and get_user_role(current_user.login)
    ):
        try:
            file = form_file.file_text.data
            file_name = form_file.file_name_text.data
            logger.debug("Полученно из формы данных для загрузки в RAG базу")
        except Exception as err:
            logger.error(
                f"Не удалось получить данные из формы для загрузки в RAG базу Ошибка:{err}"
            )
        chunks = chunk_create(file)
        norm_text = normalize_text(file)
        add_docs(chunks, file_name, norm_text)
        redirect(request.referrer)
    return render_template(
        "admin/docs.html",
        admin=current_user.login,
        form_file=form_file,
        nav=nav,
    )


@user_app.route("/admin/config", methods=["GET", "POST"])
@login_required
def admin_config_api():
    nav = check_nav(current_user.login)
    form = Config_update()
    form_textaria=Config_update_textaria()
    if (
        (form.config_value.data or form_textaria.config_value.data)
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
        form_textaria=form_textaria,
        configs=get_configs(),
        nav=nav,
    )
