from fastapi import APIRouter,Response
from pydantic import BaseModel
from typing import Any

from api.api_auth import UserToken
from db_modules.db_query import admin_auth_check
from db_modules.db_query_config import get_configs_ai_query,get_configs_query,update_config_ai_query,update_config_query

config_app=APIRouter(prefix='/configs',tags=['Конфиги'])

class ConfigUpdate(BaseModel):
    name:str
    value: Any

@config_app.get('/ai',summary='Получение конфигов AI')
async def get_configs_ai_api(token_data:UserToken,response:Response):
    auth=admin_auth_check(login=token_data.login,token=token_data.user_token)
    if auth==True:
        result=get_configs_ai_query()
    else:
        result={'result':False,'message':"Доступно только администратору", 'category':"warning",'cod':401}
    response.status_code=result['cod']
    del result['cod']
    return result

@config_app.get('/app',summary='Получение конфигов приложения')
async def get_configs_ai_api(token_data:UserToken,response:Response):
    auth=admin_auth_check(login=token_data.login,token=token_data.user_token)
    if auth==True:
        result=get_configs_query()
    else:
        result={'result':False,'message':"Доступно только администратору", 'category':"warning",'cod':401}
    response.status_code=result['cod']
    del result['cod']
    return result

@config_app.put('/ai/update',summary='Обновление конфига AI')
async def get_configs_ai_api(token_data:UserToken,config_data:ConfigUpdate,response:Response):
    auth=admin_auth_check(login=token_data.login,token=token_data.user_token)
    if auth==True:
        result=update_config_ai_query(name=config_data.name,value=config_data.value)
    else:
        result={'result':False,'message':"Доступно только администратору", 'category':"warning",'cod':401}
    response.status_code=result['cod']
    del result['cod']
    return result

@config_app.put('/app/update',summary='Обновление конфига приложения')
async def get_configs_ai_api(token_data:UserToken,config_data:ConfigUpdate,response:Response):
    auth=admin_auth_check(login=token_data.login,token=token_data.user_token)
    if auth==True:
        result=update_config_query(name=config_data.name,value=config_data.value)
    else:
        result={'result':False,'message':"Доступно только администратору", 'category':"warning",'cod':401}
    response.status_code=result['cod']
    del result['cod']
    return result