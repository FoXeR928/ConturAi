from loguru import logger
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SubmitField,
    HiddenField,
    BooleanField,
    SelectField,
)
from wtforms.validators import DataRequired, Length

from db.db_query_users import get_user_role


def check_nav(login):
    nav = {"chats.chats_get_api": "Чаты"}
    if get_user_role(login):
        nav["admin_chats.admin_chats_api"] = "Администрирование чатов"
        nav["admin_users.admin_users_api"] = "Пользователи"
        nav["admin_chats.admin_chats_api"] = "Документы"
        nav["admin_config.admin_config_api"] = "Конфигурации"
    nav["auth.logout_api"] = "Выйти"
    logger.trace("Генерация ссылок навигации")
    return nav


class Auth(FlaskForm):
    login = StringField(
        "Логин",
        validators=[DataRequired(), Length(min=1)],
        render_kw={"class": "login_auth -input"},
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(), Length(min=1)],
        render_kw={"class": "pass_auth -input"},
    )
    remember_auth = BooleanField(
        "Запомнить", render_kw={"class": "button_auth -button"}
    )
    send = SubmitField("Войти")


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


class Create_chat(FlaskForm):
    chat = StringField(
        "Название чата",
        validators=[DataRequired(), Length(min=1)],
        render_kw={"placeholder": "Название чата"},
    )
    send_chat = SubmitField("Создать")


class Delet_chat(FlaskForm):
    chat_id = HiddenField("ID чата", validators=[DataRequired(), Length(min=1)])
    send_del = SubmitField("Удалить")


class Delet_chats_irrevocably(FlaskForm):
    send_del_chats = SubmitField("Удалить все чаты отмеченные на удаление безвозвратно")


class Send_message(FlaskForm):
    chat_id=HiddenField("ID чата", validators=[DataRequired(), Length(min=1)])
    message = StringField("Текст", validators=[DataRequired(), Length(min=1)])
    send_message = SubmitField("Отправить")


class Create_user(FlaskForm):
    login_reg = StringField("Логин", validators=[DataRequired(), Length(min=1)])
    user_name_reg = StringField("Имя", validators=[DataRequired(), Length(min=1)])
    password_reg = PasswordField(
        "Пароль",
        validators=[DataRequired(), Length(min=8)],
        render_kw=({"class": "password -input"}),
    )
    password_reg_check = PasswordField(
        "Пароль повторно",
        validators=[DataRequired(), Length(min=8)],
        render_kw=({"class": "password_check -input"}),
    )
    send_reg = SubmitField("Создать")


class Update_password(FlaskForm):
    login_update = StringField(
        "Пользоватль",
        validators=[DataRequired(), Length(min=1)],
        render_kw={"readonly": ""},
    )
    role_update = SelectField(
        "Выбор роли",
        choices=[
            (None, "Выбрать роль пользователя"),
            ("user", "Пользователь"),
            ("admin", "Администратор"),
        ],
    )
    password_update = PasswordField(
        "Пароль", validators=[Length(min=8)], render_kw=({"class": "password -input"})
    )
    password_update_check = PasswordField(
        "Пароль повторно",
        validators=[Length(min=8)],
        render_kw=({"class": "password_check -input"}),
    )
    send_update = SubmitField("Изменить")

class Delet_user(FlaskForm):
    user_login=HiddenField("Логин пользователя", validators=[DataRequired(), Length(min=1)])
    send_del=SubmitField('Удалить пользователя')

class File_text(FlaskForm):
    file_name_text = StringField(
        "Имя файла", validators=[DataRequired(), Length(min=1)]
    )
    file_text = TextAreaField("Текст файла", validators=[DataRequired(), Length(min=1)])
    send_text = SubmitField("Загрузить")
