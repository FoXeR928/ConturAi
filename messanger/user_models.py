from flask_login import login_required, current_user
from flask import render_template, request, redirect, flash
from flask.blueprints import Blueprint

from loguru import logger

from messanger.moduls import check_nav, Create_chat, Delet_chat, Send_message
from db.db_query_chat import (
    get_chats,
    get_messages_chat,
    get_messages_ai,
    create_chat,
    create_message,
    delet_messages,
)
from ai_chat.ask import ask_query

try:
    logger.debug("Инициализация пути /users")
    user_app = Blueprint("user", __name__, url_prefix="/user")
except Exception as err:
    logger.error(f"Инициализация пути /users не удалась Ошибка:{err}")


@user_app.route("/chats", methods=["GET", "POST"])
@login_required
def user_get_create_chats_api():
    form = Create_chat()
    form_del = Delet_chat()
    if form.send_chat.data and form.validate_on_submit():
        try:
            chat = form.chat.data
            logger.debug("Полученно имя чата из формы")
        except Exception as err:
            logger.error(f"Не удалось получить поле с именем чата Ошибка:{err}")
        create_chat(current_user.login, chat)
        return redirect(request.referrer)
    if form_del.send_del.data and form_del.validate_on_submit():
        try:
            chat = form_del.chat_id.data
            logger.debug("Полученно ID чата из формы")
            delet_messages(chat_id=chat)
        except Exception as err:
            logger.error(f"Не удалось получить поле с именем чата Ошибка:{err}")
        return redirect(request.referrer)
    return render_template(
        "chats/user_chats.html",
        chats=get_chats(current_user.login),
        form=form,
        form_del=form_del,
        login=current_user.login,
        nav=check_nav(current_user.login),
    )


@user_app.route("/chats/<chat>", methods=["GET", "POST"])
@login_required
def user_get_chat_api(chat: str):
    messages = get_messages_chat(login=current_user.login, chat_id=chat)
    form = Send_message()
    if form.validate_on_submit():
        try:
            text = form.message.data
            logger.debug("Полученно сообщения из формы чата")
        except Exception as err:
            logger.error(f"Не удалось получить поле с сообщением чата Ошибка:{err}")
        messages_history = get_messages_ai(chat)
        if messages_history != None:
            create_message(login=current_user.login, chat_id=chat, text=text)
            ask_query(query=text, chat_id=chat, messages_history=messages_history)
        return redirect(request.referrer)
    return render_template(
        "chats/chat.html",
        messages=messages["messages"],
        form=form,
        chat_name=messages["name"],
        chat_id=chat,
        login=current_user.login,
    )
