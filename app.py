from flask import Flask, render_template,redirect,url_for,flash
from flask_login import LoginManager
from loguru import logger
from sys import stdout
from sqlalchemy import select
import os
import json

from db.db_create import db
from messanger.moduls import Settings,Settings_ai


def init_db():
    try:
        db.init_app(app=app)
        with app.app_context():
            db.create_all()
            from db.db_create_default import create_default_config,create_default_users

            create_default_config()
            create_default_users()
        logger.debug(f"Инициализация SQL_FLASK")
    except Exception as err:
        logger.critical(f"Не удалось инициализировать SQL_FLASK Ошибка:{err}")
        exit()

def init_pages():
    try:
        from messanger import admin_chats_moduls, auth_moduls, chats_moduls,admin_users_moduls,admin_ai_moduls,admin_configs_moduls,admin_moduls

        app.register_blueprint(auth_moduls.auth_app)
        app.register_blueprint(chats_moduls.chats_app)
        app.register_blueprint(admin_moduls.admin_app)
        app.register_blueprint(admin_users_moduls.admin_users_app)
        app.register_blueprint(admin_chats_moduls.admin_chats_app)
        app.register_blueprint(admin_configs_moduls.admin_config_app)
        app.register_blueprint(admin_ai_moduls.admin_ai_app)
    except Exception as err:
        logger.critical(f"Не удалось инициализировать страницы Ошибка:{err}")
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

if not os.path.exists('config.json'):
    data={
        'CREATE_CONFIG':True,
        'CREATE_AI':True,
        'PORT':7000,
        'DEBUG':True
        }
    with open("config.json", "w") as file_config:
        json.dump(data,file_config,indent=4)

try:
    app = Flask(__name__)
    app.secret_key=os.urandom(24)
    app.config.from_file('config.json',load=json.load)
    PORT=app.config['PORT']
    DEBUG=app.config['DEBUG']
    if not app.config['CREATE_CONFIG']:
        init_db()
    if not app.config['CREATE_AI']:
        init_pages()
    init_log()
    logger.debug("Добавление конфигов Flask")
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
        user=db.session.scalars(select(Users).where(Users.id == id)).one()
    except Exception as err:
        logger.critical(f"Не удалось инициализировать авторизацию Ошибка:{err}")
    return user

@app.get('/')
def index():
    if app.config['CREATE_CONFIG']:
        return redirect(url_for('start_settings'))
    elif app.config['CREATE_AI']:
        return redirect(url_for('start_settings_ai'))
    else:
        return redirect(url_for('auth.auth_api'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("not_found.html"), 404

@app.get('/start_settings')
def start_settings():
    form=Settings()
    return render_template('settings.html',form=form)

@app.get('/start_settings_ai')
def start_settings_ai():
    form=Settings_ai()
    return render_template('settings_ai.html',form=form)

@app.post('/create_start_settings')
def create_start_settings():
    form=Settings()
    if form.send_settings.data and form.validate_on_submit():
        port=form.port.data
        debug=form.debug.data
        db_select=form.db_select.data
        db_server=form.db_server.data
        db_path=form.db_path.data
        db_name=form.db_name.data
        db_port=form.db_port.data
        db_user=form.db_user.data
        db_password=form.db_password.data
        if db_select=='sqlite':
            db_url=f'sqlite:///{db_path}'
        elif db_select=='postgres':
            db_url=f'postgresql://{db_user}:{db_password}@{db_server}:{db_port}/{db_name}'
        data={
        'CREATE_CONFIG':False,
        'CREATE_AI':True,
        'PORT':port,
        'DEBUG':debug,
        'SQLALCHEMY_DATABASE_URI':db_url
        }
        with open("config.json", "w") as file_config:
            json.dump(data,file_config,indent=4)
        flash(message='Файл конфигов создан',category='success')
        init_db()
    else:
        flash(message='Файл конфигов не создан',category='warning')
    return redirect(url_for('index'))

@app.post('/create_start_settings')
def create_start_settings_ai():
    form=Settings()
    if form.send_settings.data and form.validate_on_submit():
        port=form.port.data
        debug=form.debug.data
        db_select=form.db_select.data
        db_server=form.db_server.data
        db_path=form.db_path.data
        db_name=form.db_name.data
        db_port=form.db_port.data
        db_user=form.db_user.data
        db_password=form.db_password.data
        if db_select=='sqlite':
            db_url=f'sqlite:///{db_path}'
        elif db_select=='postgres':
            db_url=f'postgresql://{db_user}:{db_password}@{db_server}:{db_port}/{db_name}'
        data={
        'CREATE_CONFIG':False,
        'CREATE_AI':True,
        'PORT':port,
        'DEBUG':debug,
        'SQLALCHEMY_DATABASE_URI':db_url
        }
        with open("config.json", "w") as file_config:
            json.dump(data,file_config,indent=4)
        flash(message='Файл конфигов создан',category='success')
        init_db()
    else:
        flash(message='Файл конфигов не создан',category='warning')
    return redirect(url_for('index'))

if __name__ == "__main__":
    try:
        logger.info(f"Приложение запущено на порту {PORT}")
        app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
    except Exception as err:
        logger.critical(f"Не удалось запустить Flask Ошибка:{err}")
        exit()
