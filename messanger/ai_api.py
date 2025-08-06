from flask_login import login_required, current_user
from flask import request, redirect, flash
from flask.blueprints import Blueprint
from loguru import logger

from db.db_query_chat import (
    get_messages_ai,
    create_message,
)
from ai_chat.ask import ask_query
from ai_chat.query_rag_db import add_docs
from ai_chat.parther import normalize_text, chunk_create
from db.db_query_users import get_user_role
from messanger.moduls import File_text

try:
    logger.debug("Инициализация пути /api/ai")
    api_ai_app = Blueprint("api_ai", __name__, url_prefix="/api/ai")
except Exception as err:
    logger.error(f"Инициализация пути /api/ai не удалась Ошибка:{err}")

@api_ai_app.post("/create_message")
@login_required
def create_message_api():
    if request.method == "POST":
        try:
            chat = request.form["chat_id"]
            text = request.form["message"]
            logger.debug("Полученно сообщения из формы чата")
        except Exception as err:
            logger.error(f"Не удалось получить поле с сообщением чата Ошибка:{err}")

        messages_history = get_messages_ai(chat)
        if messages_history != None:
            create_message(login=current_user.login, chat_id=chat, text=text)
            ask_query(query=text, chat_id=chat, messages_history=messages_history)
    else:
        flash(
            message="Сообщение не удален, неправельно заполнены поля",
            category="warning",
        )
    return redirect(request.referrer)

@api_ai_app.post("/add_docs")
@login_required
def ai_add_docs_api():
    if get_user_role(current_user.login):
        try:
            file = request.form['file_text']
            file_name = request.form['file_name_text']
            logger.debug("Полученно из формы данных для загрузки в RAG базу")
        except Exception as err:
            logger.error(
                f"Не удалось получить данные из формы для загрузки в RAG базу Ошибка:{err}"
            )
        chunks = chunk_create(file)
        norm_text = normalize_text(file)
        add_docs(chunks, file_name, norm_text)
    return redirect(request.referrer)