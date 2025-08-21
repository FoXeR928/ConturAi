from fastapi import APIRouter,Response
from pydantic import BaseModel

from db_modules.db_query import admin_auth_check,user_auth_check,check_user
from db_modules.db_query_auth import auth_query,logout_query,get_token_query,create_token_query

auth_app=APIRouter(prefix='/auth',tags=['Авторизация'])

class Auth(BaseModel):
    login:str
    password:str

class UserToken(BaseModel):
    login:str
    user_token:str

@auth_app.post('/',summary='Авторизация для получения токена')
async def auth_api(auth_data:Auth,response:Response):
    user=check_user(login=auth_data.login)
    if user==True:
        result=auth_query(login=auth_data.login,password=auth_data.password)
    else:
        result={'result':False,'message':"Неверный логин или пароль", 'category':"warning",'cod':401}
    response.status_code=result['cod']
    del result['cod']
    return result

@auth_app.post('/logout',summary='Выход из учетной записи')
async def auth_api(token_data:UserToken,response:Response):
    auth=user_auth_check(login=token_data.login,token=token_data.user_token)
    if auth==True:
        result=logout_query(login=token_data.login)
    else:
        result={'result':False,'message':"Авторизация не пройдена", 'category':"warning",'cod':401}
    response.status_code=result['cod']
    del result['cod']
    return result

@auth_app.get('/get_token',summary='Получени токена API')
async def get_token_api(token_data:UserToken,response:Response):
    auth=admin_auth_check(login=token_data.login,token=token_data.user_token)
    if auth==True:
        result=get_token_query()
    else:
        result={'result':False,'message':"Доступно только администратору", 'category':"warning",'cod':401}
    response.status_code=result['cod']
    del result['cod']
    return result

@auth_app.put('/create_token',summary='Создание токена API')
async def create_token_api(token_data:UserToken,response:Response):
    auth=admin_auth_check(login=token_data.login,token=token_data.user_token)
    if auth==True:
        result=create_token_query()
    else:
        result={'result':False,'message':"Доступно только администратору", 'category':"warning",'cod':401}
    response.status_code=result['cod']
    del result['cod']
    return result