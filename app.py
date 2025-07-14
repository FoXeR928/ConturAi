from flask import Flask, render_template
from flask_login import LoginManager
from loguru import logger
from sys import stdout

from db.db_create import db
from config.config import PORT, SQL_PATH, SKEY, DEBUG, HOST, LOG_DAYS, LOG_SIZE

def init_pages():
    try:
        from messanger import admin_models, auth_models, user_models

        app.register_blueprint(admin_models.admin_app)
        app.register_blueprint(auth_models.auth_app)
        app.register_blueprint(user_models.user_app)
    except Exception as err:
        logger.critical(f"Не удалось инициализировать страницы Ошибка:{err}")
        exit()


def init_log(log_level_file="INFO",log_level_std="WARNING"):
    logger.remove()
    logger.add(
        "logs/log_{time}.log",
        format="{time} | {level} | {message} | {name}",
        rotation=LOG_SIZE,
        retention=f"{LOG_DAYS} days",
        level=log_level_file
    )
    if DEBUG:
        log_level_std="TRACE"
    logger.add(stdout, level=log_level_std)


init_log()
try:
    app = Flask(__name__)
    logger.debug(f"Инициализация Flask")
    app.config["SECRET_KEY"] = SKEY
    app.config["SQLALCHEMY_DATABASE_URI"] = SQL_PATH
    logger.debug("Добавление конфигов Flask")
except Exception as err:
    logger.critical(f"Не удалось инициализировать приложение Flask Ошибка:{err}")
    exit()

try:
    login_manager = LoginManager(app=app)
    login_manager.login_view = "auth.login_api"
    logger.debug(f"Инициализация авторизации")
except Exception as err:
    logger.critical(f"Не удалось инициализировать авторизацию Ошибка:{err}")
    exit()

try:
    db.init_app(app=app)
    with app.app_context():
        db.create_all()
        from db.db_create_default import create_default_users, create_default_config
        create_default_users()
        create_default_config()
    logger.debug(f"Инициализация SQL_FLASK")
except Exception as err:
    logger.critical(f"Не удалось инициализировать SQL_FLASK Ошибка:{err}")
    exit()



init_pages()

@login_manager.user_loader
def load_user(id):
    from db.db_create import Users

    return db.session.query(Users).filter(Users.id == id).one()


@app.errorhandler(404)
def page_not_found(e):
    return render_template("not_found.html"),404


if __name__ == "__main__":
    try:
        logger.info(f'Приложение запущено на порту {PORT}')
        app.run(debug=DEBUG, host=HOST, port=PORT)
    except Exception as err:
        logger.critical(f"Не удалось запустить Flask Ошибка:{err}")
        exit()
