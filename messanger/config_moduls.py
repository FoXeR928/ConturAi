from flask import render_template, redirect, flash,url_for
from flask.blueprints import Blueprint
import json
from loguru import logger

from messanger.moduls import Settings,Settings_ai
from db.db_query_config import create_config_ai_start

try:
    logger.debug("Инициализация пути /settings")
    configs_app = Blueprint(name="settings", import_name=__name__, url_prefix="/settings")
except Exception as err:
    logger.error(f"Инициализация пути /settings не удалась Ошибка:{err}")


@configs_app.get('/start_settings')
def start_settings():
    form=Settings()
    from app import app
    if app.config['CREATE_CONFIG']==True:
        return render_template('settings.html',form=form)
    else:
        return redirect(url_for('settings.create_start_settings_ai'))

@configs_app.get('/start_settings_ai')
def start_settings_ai():
    form=Settings_ai()
    return render_template('settings_ai.html',form=form)

@configs_app.post('/create_start_settings')
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
        'DEBUG_FLASK':True,
        'SQLALCHEMY_DATABASE_URI':db_url
        }
        with open("instance/config.json", "w") as file_config:
            json.dump(data,file_config,indent=4)
        from app import init_db
        init_db()
        flash(message='Файл конфигов создан',category='success')
    else:
        flash(message='Файл конфигов не создан',category='warning')
    return redirect(url_for('index'))

@configs_app.post('/create_start_settings_ai')
def create_start_settings_ai():
    form=Settings_ai()
    if form.send_settings_ai.data and form.validate_on_submit():
        model_chunk=form.model_chunk.data
        model=form.model.data
        collection=form.collection.data
        rag_host=form.rag_host.data
        rag_port_http=form.rag_port_http.data
        rag_port_grpc=form.rag_port_grpc.data
        rag_grpc=form.rag_grpc.data
        config_to_add={'model_chunk':model_chunk,'model':model,'collection':collection,'rag_host':rag_host,'rag_port_http':rag_port_http,'rag_port_grpc':rag_port_grpc,'rag_grpc':rag_grpc}
        create_config_ai_start(config_to_add)
        with open("./instance/config.json", "r") as file_config_read:
            config=json.load(file_config_read)
            config['CREATE_AI']=False
            config['DEBUG_FLASK']=False
            with open("instance/config.json", "w") as file_config:
                json.dump(config,file_config,indent=4)
        flash(message='Файл конфигов создан',category='success')
        from app import init_pages
        init_pages()
    else:
        flash(message='Файл конфигов не создан',category='warning')
    return redirect(url_for('index'))