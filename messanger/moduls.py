from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    IntegerField,
    PasswordField,
    TextAreaField,
    SubmitField,
    HiddenField,
    BooleanField,
    SelectField,
)
from wtforms.validators import DataRequired, Length


class Settings(FlaskForm):
    port = IntegerField(
        "Порт сервера",
        validators=[DataRequired()],
        render_kw={"class": "port -input", "value": 7000},
    )
    debug = BooleanField(
        "Подробное логирование", render_kw={"class": "check_debug -checkbox"}
    )
    db_select = SelectField(
        "База данных",
        choices=[
            (None, "Выбор базы данных"),
            ("sqlite", "SQLite"),
            ("postgres", "PostgresSQL"),
        ],
    )
    db_server = StringField(
        "Хост сервера БД",
        validators=[DataRequired()],
        render_kw={"class": "db_server -input -hide -server"},
    )
    db_path = StringField(
        "Путь БД",
        validators=[DataRequired()],
        render_kw={"class": "db_path -input -hide -local"},
    )
    db_port = IntegerField(
        "Порт сервера БД",
        validators=[DataRequired()],
        render_kw={
            "class": "db_port -input -hide -server",
        },
    )
    db_user = StringField(
        "Пользователь БД",
        validators=[DataRequired()],
        render_kw={"class": "db_login -input -hide -server"},
    )
    db_password = PasswordField(
        "Пароль БД",
        validators=[DataRequired()],
        render_kw={"class": "db_password -input -hide -server"},
    )
    db_name = StringField(
        "База БД",
        validators=[DataRequired()],
        render_kw={"class": "db_name -input -hide -server"},
    )
    send_settings = SubmitField("Сохранить", render_kw={"class": "button_send -button"})


class Settings_ai(FlaskForm):
    model_chunk = StringField(
        "Модель для создания чанков",
        validators=[DataRequired()],
        render_kw={
            "class": "model_chunk -input",
            "value": "./ai_chat/models/sbert_large_nlu_ru",
        },
    )
    model = StringField(
        "Модель AI",
        validators=[DataRequired()],
        render_kw={"class": "model -input", "value": "ilyagusev/saiga_llama3"},
    )
    collection = StringField(
        "Имя коллекции",
        validators=[DataRequired()],
        render_kw={"class": "collection -input", "value": "ragi_docs"},
    )
    rag_host = StringField(
        "Хост Qdrant",
        validators=[DataRequired()],
        render_kw={"class": "rag_host -input", "value": "localhost"},
    )
    rag_port_http = IntegerField(
        "Порт HTTP Qdrant",
        validators=[DataRequired()],
        render_kw={"class": "rag_port_http -input", "value": 6333},
    )
    rag_port_grpc = IntegerField(
        "Порт GRPC Qdrant",
        validators=[DataRequired()],
        render_kw={"class": "rag_port_grpc -input", "value": 6334},
    )
    rag_grpc = BooleanField(
        "Включить GRPC",
        render_kw={"class": "rag_grpc -input"},
    )
    send_settings_ai = SubmitField(
        "Сохранить", render_kw={"class": "button_send -button"}
    )


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
        "Запомнить", render_kw={"class": "check_auth -checkbox"}
    )
    send = SubmitField("Войти", render_kw={"class": "button_auth -button"})


class Create_chat(FlaskForm):
    chat = StringField(
        "Название чата",
        validators=[DataRequired(), Length(min=1)],
        render_kw={"placeholder": "Название чата", "class": "name_chat -separete_main -input_separete"},
    )
    send_chat = SubmitField(
        "Создать",
        render_kw={"class": "send_message -separete_second -button_separete"},
    )

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
    user_login = HiddenField(
        "Логин пользователя", validators=[DataRequired(), Length(min=1)]
    )
    send_del = SubmitField("Удалить пользователя")


class File_text(FlaskForm):
    file_name_text = StringField(
        "Имя файла", validators=[DataRequired(), Length(min=1)]
    )
    file_text = TextAreaField("Текст файла", validators=[DataRequired(), Length(min=1)])
    send_text = SubmitField("Загрузить")
