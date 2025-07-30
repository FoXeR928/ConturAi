from flask_login import login_required, current_user
from flask import render_template, request, redirect, flash, abort
from flask.blueprints import Blueprint

from loguru import logger

from messanger.moduls import Create_chat
from db.db_query_chat import (
    get_chats,
    get_messages_chat,
    get_messages_ai,
    create_chat,
    create_message,
    delet_messages,
)
from db.db_query_users import get_user_role
from ai_chat.ask import ask_query

try:
    logger.debug("Инициализация пути /chats")
    chats_app = Blueprint("chats", __name__, url_prefix="/chats")
except Exception as err:
    logger.error(f"Инициализация пути /chats не удалась Ошибка:{err}")


@chats_app.get("")
@login_required
def chats_get_api():
    form = Create_chat()
    return render_template(
        "chats/user_chats.html",
        chats=get_chats(current_user.login),
        form=form,
        login=current_user.login,
        isAdmin=get_user_role(current_user.login),
    )


@chats_app.post("/create_chat")
@login_required
def create_chat_api():
    form = Create_chat()
    if form.send_chat.data and form.validate_on_submit():
        try:
            chat = form.chat.data
            logger.debug("Полученно имя чата из формы")
        except Exception as err:
            logger.error(f"Не удалось получить поле с именем чата Ошибка:{err}")
        create_chat(current_user.login, chat)
    else:
        flash(message="Чат не создан неправельно заполнены поля", category="warning")
    return redirect(request.referrer)


@chats_app.get("/delet_chat/<chat>")
@login_required
def delet_chat_api(chat: str):
    delet_messages(chat_id=chat, user=current_user.login)
    logger.debug("Полученно ID чата из формы")
    return redirect(request.referrer)


@chats_app.get("/<chat>")
@login_required
def get_chat_api(chat: str):
    messages = get_messages_chat(login=current_user.login, chat_id=chat)
    if messages == False:
        abort(404)
    return render_template(
        "chats/chat.html",
        messages=messages["messages"],
        chat_name=messages["name"],
        chat_id=chat,
        login=current_user.login,
        isAdmin=get_user_role(login=current_user.login),
        chats=get_chats(login=current_user.login),
    )


@chats_app.post("/create_message")
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
