from flask_login import login_required, current_user
from flask import request, redirect, jsonify,flash,render_template
from flask.blueprints import Blueprint
from io import BytesIO
from loguru import logger

from messanger.moduls import check_nav,Create_user,Update_password,Config_update,Config_update_textaria,File_text,Delet_chats_irrevocably
from db.db_query_admin import add_user_status, add_file, get_config, del_chats, update_config, get_configs,get_users,reg_user, get_del_chats
from db.db_query import get_user_role,update_password_user
from ai_chat.parther import read_pdf, read_word, read_excel
from ai_chat.query_rag_db import add_docs
from ai_chat.parther import normalize_text, chunk_create

try:
    logger.debug("Инициализация пути /admin")
    admin_app = Blueprint("admin", __name__, url_prefix="/admin")
except Exception as err:
    logger.error(f"Инициализация пути /admin не удалась Ошибка:{err}")

@admin_app.route("/chats", methods=["GET", "POST"])
@login_required
def admin_chats_api():
    form_del_irr=Delet_chats_irrevocably()
    if form_del_irr.send_del_chats.data:
        del_chats()
        logger.debug('Отправлен запрос на удаление всех чатов')
        return redirect(request.referrer)
    return render_template(
        "admin/admin_chats.html",
        form_del_irr=form_del_irr,
        chats=get_del_chats(),
        nav=check_nav(current_user.login),
    )

@admin_app.route("/users", methods=["GET", "POST"])
@login_required
def admin_users_api():
    form_user = Create_user()
    form_password = Update_password()
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
        and get_user_role(current_user.login)
    ):
        try:
            login = form_password.login_update.data
            password = form_password.password_update.data
            role=form_password.role_update.data
            logger.debug(
                "Полученно из формы данных пользователя для обновления информации пользователя"
            )
        except Exception as err:
            logger.error(
                f"Не удалось получить данные из формы для смены пароля пользователя админом Ошибка:{err}"
            )
            flash(message='Не удалось получить значения на изменение',category='warning')
            redirect(request.referrer)
        if password!='' and role!='None':
            try:
                update_password_user(
                        login=login, password=password, user_update_password=current_user.login
                )
                add_user_status(login=login, role=role)
                logger.trace(f"Выполнен API запрос на смену пароля и роли пользователя {login}")
                flash(message='Пароль и роль изменены',category='success')
            except Exception as err:
                logger.error(f"Невыполнен API запрос на смену пароля и роли пользователя {login} статуса Ошибка: {err}")
                flash(message=f"Невыполнен API запрос на смену пароля и роли пользователя {login} статуса Ошибка: {err}",category='error')
        elif password!='':
            try:
                update_password_user(
                        login=login, password=password, user_update_password=current_user.login
                )
                logger.trace(f"Выполнен API запрос на смену пароля пользователя {login}")
                flash(message='Пароль изменен',category='success')
            except Exception as err:
                logger.error(f"Невыполнен API запрос на смену пароля пользователя {login} статуса Ошибка: {err}")
                flash(message=f"Невыполнен API запрос на смену пароля пользователя {login} статуса Ошибка: {err}",category='error')
        elif role!='None':
            try:
                add_user_status(login=login, role=role)
                logger.debug(f"Выполнен API запрос на смену роли пользователя {login}")
            except Exception as err:
                logger.error(f"Невыполнен API запрос на смену роли пользователя {login} Ошибка:{err}")
        else:
            flash(message='Нет значений на изменение',category='warning')
        return redirect(request.referrer)
    return render_template(
        "admin/users.html",
        admin=current_user.login,
        form_user=form_user,
        form_password=form_password,
        users=get_users(),
        nav=check_nav(current_user.login),
    )

@admin_app.route("/config", methods=["GET", "POST"])
@login_required
def admin_config_api():
    nav = check_nav(current_user.login)
    form = Config_update()
    form_textaria = Config_update_textaria()
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

@admin_app.patch("/del_chats")
@login_required
def admin_del_chats_api():
    form_del=Delet_chats_irrevocably()
    try:
        if form_del.send_del_chats.data:
            del_chats()
            logger.debug("Выполнен API запрос на безвозвратное удаление чатов")
    except Exception as err:
        logger.error(f"Невыполнен API запрос на безвозвратное удаление чатов Ошибка:{err}")
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
