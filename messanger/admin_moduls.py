from flask_login import login_required, current_user
from flask import request, redirect, jsonify, flash, render_template
from flask.blueprints import Blueprint
from io import BytesIO
from loguru import logger

from messanger.moduls import (
    check_nav,
    File_text,
)
from db.db_query_admin import ( 
    add_file,
    get_config,
)
from db.db_query_users import get_user_role
from ai_chat.parther import read_pdf, read_word, read_excel
from ai_chat.query_rag_db import add_docs
from ai_chat.parther import normalize_text, chunk_create

try:
    logger.debug("Инициализация пути /admin")
    admin_app = Blueprint("admin", __name__, url_prefix="/admin")
except Exception as err:
    logger.error(f"Инициализация пути /admin не удалась Ошибка:{err}")





@admin_app.route("/docs", methods=["GET", "POST"])
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
