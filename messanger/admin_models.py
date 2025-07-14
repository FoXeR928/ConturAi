from flask_login import login_required, current_user
from flask import request, redirect, jsonify
from flask.blueprints import Blueprint
from io import BytesIO
from loguru import logger

from db.db_query_admin import add_user_status, add_file, get_config
from db.db_query import update_password_user, get_user_role
from ai_chat.parther import read_pdf, read_word, read_excel

try:
    logger.debug("Инициализация пути /admin")
    admin_app = Blueprint("admin", __name__, url_prefix="/admin")
except Exception as err:
    logger.error(f"Инициализация пути /admin не удалась Ошибка:{err}")


@admin_app.patch("/set_status")
@login_required
def admin_set_status_api(login: str, role: str):
    try:
        add_user_status(login, role, current_user.login)
        logger.debug("Выполнен API запрос на смену статуса")
    except Exception as err:
        logger.error(f"Невыполнен API запрос на смену статуса Ошибка:{err}")
    return redirect(request.referrer)


@admin_app.patch("/update_password")
@login_required
def admin_set_password_api():
    try:
        login=request.values['login_user']
        password=request.values['password_update']
        logger.trace("Получены запросы")
        if login==current_user.login or get_user_role(current_user.login):
            update_password_user(login=login, password=password, user_update_password=current_user.login)
            logger.trace("Выполнен API запрос на смену статуса")
        else:
            logger.debug(f"Пользователь {current_user.login} не имеет право на смену пароля")
    except Exception as err:
        logger.error(f"Невыполнен API запрос на смену статуса Ошибка:{err}")
    return redirect(request.referrer)


@admin_app.post("/read_file")
@login_required
def read_file_api():
    try:
        file = request.files["file"]
        file_name = file.filename
        file_dytes = BytesIO(file.read())
        logger.debug("Получена информация из файла для парсинга")
    except Exception as err:
        logger.error(f"Невыполнен API запрос на смену статуса Ошибка:{err}")
        return jsonify(
            {
                "name": "Ошибка получения информации файла",
                "text": "Ошибка получения информации файла",
            }
        )
    try:
        if file.content_type == get_config("pdf"):
            file_type = "pdf"
            file_text = read_pdf(file_dytes)
        elif file.content_type == get_config("word"):
            file_type = "docx"
            file_text = read_word(file_dytes)
        elif file.content_type == get_config("excel"):
            file_type = "xlsx"
            file_text = read_excel(file_dytes)
        logger.debug("Файл прочитан")
    except Exception as err:
        logger.error(
            f"Не удалось прочитать файл и отправить на запись в базу Ошибка:{err}"
        )
        return jsonify({"name": "Ошибка чтения файла", "text": "Ошибка чтения файла"})
    add_file(file_dytes, file_type, file_name)
    return jsonify({"name": file_name, "text": file_text})
