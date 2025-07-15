from loguru import logger
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SubmitField,
    HiddenField,
    BooleanField
)
from wtforms.validators import DataRequired, Length

from db.db_query import get_user_role

def check_nav(login):
    nav = {"user.user_get_create_chats_api": "Чаты"}
    if get_user_role(login):
        nav["admin.admin_chats_api"] = "Администрирование чатов"
        nav["admin.admin_users_api"] = "Пользователи"
        nav["admin.admin_docs_api"] = "Документы"
        nav["admin.admin_config_api"] = "Конфигурации"
    nav["auth.logout_api"] = "Выйти"
    logger.trace("Генерация ссылок навигации")
    return nav

class Auth(FlaskForm):
    login = StringField("Логин", validators=[DataRequired(), Length(min=1)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=1)])
    remember_auth = BooleanField("Запомнить")
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
    chat = StringField("Название чата", validators=[DataRequired(), Length(min=1)])
    send_chat = SubmitField("Создать")

class Delet_chat(FlaskForm):
    chat_id=HiddenField('ID чата', validators=[DataRequired(), Length(min=1)])
    send_del = SubmitField("Удалить")

class Delet_chats_irrevocably(FlaskForm):
    send_del_chats=SubmitField('Удалить все чаты отмеченные на удаление безвозвратно')

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