from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from loguru import logger
from sys import stdout
from sqlalchemy import select
import os
import json

from db.db_create import db


def init_db():
    try:
        app.config.from_file("instance/config.json", load=json.load)
        db.init_app(app=app)
        with app.app_context():
            db.create_all()
            from db.db_create_default import (
                create_default_config,
                create_default_users,
                create_default_config_ai,
            )

            create_default_config()
            create_default_config_ai()
            create_default_users()
        logger.debug(f"Инициализация SQL_FLASK")
    except Exception as err:
        logger.critical(f"Не удалось инициализировать SQL_FLASK Ошибка:{err}")
        exit()


def init_pages():
    try:
        app.config.from_file("instance/config.json", load=json.load)
        with app.app_context():
            from messanger import (
                admin_chats_moduls,
                auth_moduls,
                chats_moduls,
                admin_users_moduls,
                admin_configs_moduls,
                admin_ai_config_moduls,
                admin_ai_docs_moduls
            )

            app.register_blueprint(auth_moduls.auth_app)
            app.register_blueprint(chats_moduls.chats_app)
            app.register_blueprint(admin_ai_config_moduls.admin_ai_config_app)
            app.register_blueprint(admin_users_moduls.admin_users_app)
            app.register_blueprint(admin_chats_moduls.admin_chats_app)
            app.register_blueprint(admin_configs_moduls.admin_config_app)
            app.register_blueprint(admin_ai_docs_moduls.admin_ai_docs_app)
    except Exception as err:
        logger.critical(f"Не удалось инициализировать страницы Ошибка:{err}")
        exit()


def init_page_settings():
    try:
        from messanger import setting_moduls

        app.register_blueprint(setting_moduls.configs_app)
    except Exception as err:
        logger.critical(f"Не удалось инициализировать страницы настроек Ошибка:{err}")
        exit()


def init_log(log_level_file="INFO", log_level_std="WARNING"):
    logger.remove()
    logger.add(
        "logs/app.log",
        format="{time} | {level} | {message} | {name}",
        rotation="256 MB",
        retention=f"10 days",
        level=log_level_file,
    )
    if DEBUG:
        log_level_std = "TRACE"
    logger.add(stdout, level=log_level_std)


if not os.path.exists("instance/config.json"):
    data = {
        "CREATE_CONFIG": True,
        "CREATE_AI": True,
        "PORT": 7000,
        "DEBUG": False,
        "DEBUG_FLASK": True,
    }
    with open("instance/config.json", "w") as file_config:
        json.dump(data, file_config, indent=4)
    logger.debug("Добавление конфигов Flask")

try:
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    app.config.from_file("instance/config.json", load=json.load)
    PORT = app.config["PORT"]
    DEBUG = app.config["DEBUG"]
    init_log()
    if app.config["CREATE_CONFIG"] == False:
        init_db()
    if app.config["CREATE_AI"] == False:
        init_pages()
    if app.config["CREATE_CONFIG"] == True or app.config["CREATE_AI"] == True:
        init_page_settings()
    logger.debug(f"Инициализация Flask")
except Exception as err:
    logger.critical(f"Не удалось инициализировать приложение Flask Ошибка:{err}")
    exit()

try:
    login_manager = LoginManager(app=app)
    login_manager.login_view = "auth.auth_api"
    logger.debug(f"Инициализация авторизации")
except Exception as err:
    logger.critical(f"Не удалось инициализировать авторизацию Ошибка:{err}")
    exit()


@login_manager.user_loader
def load_user(id):
    from db.db_create import Users

    try:
        user = db.session.scalars(select(Users).where(Users.id == id)).one()
    except Exception as err:
        logger.critical(f"Не удалось инициализировать авторизацию Ошибка:{err}")
    return user


@app.get("/")
def index():
    app.config.from_file("instance/config.json", load=json.load)
    if app.config["CREATE_CONFIG"]:
        return redirect(url_for("settings.start_settings"))
    elif app.config["CREATE_AI"]:
        return redirect(url_for("settings.start_settings_ai"))
    else:
        return redirect(url_for("auth.auth_api"))


@app.errorhandler(404)
def page_not_found(e):
    if not (app.config["CREATE_CONFIG"] and app.config["CREATE_AI"]):
        return render_template("not_found.html"), 404
    else:
        return redirect(url_for("index"))


if __name__ == "__main__":
    try:
        logger.info(f"Приложение запущено на порту {PORT}")
        app.run(
            debug=app.config["DEBUG_FLASK"],
            host="0.0.0.0",
            port=PORT,
            extra_files=["instance/config.json"],
        )
    except Exception as err:
        logger.critical(f"Не удалось запустить Flask Ошибка:{err}")
        exit()
