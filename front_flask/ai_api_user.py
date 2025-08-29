from flask_login import login_required, current_user
from flask import request, redirect, flash
from flask.blueprints import Blueprint
from loguru import logger

from ai_chat.query_rag_db import add_docs
from ai_chat.parther import normalize_text, chunk_create


@api_ai_user_app.post("/add_docs")
@login_required
def ai_add_docs_api():
    if get_user_role(current_user.login):
        try:
            file = request.form["file_text"]
            file_name = request.form["file_name_text"]
            logger.debug("Полученно из формы данных для загрузки в RAG базу")
        except Exception as err:
            logger.error(
                f"Не удалось получить данные из формы для загрузки в RAG базу Ошибка:{err}"
            )
        chunks = chunk_create(file)
        norm_text = normalize_text(file)
        add_docs(chunks, file_name, norm_text)
    return redirect(request.referrer)
