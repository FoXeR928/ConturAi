from fastapi import APIRouter,Response
from pydantic import BaseModel

from db_modules.db_query import admin_auth_check,user_auth_check,check_user
from db_modules.db_query_chat import create_chat

chat_app=APIRouter(prefix='/chats',tags=['Чаты'])

class UserToken(BaseModel):
    login:str
    user_token:str

@chat_app.post('/create',summary='Создание чата')
async def get_configs_ai_api(token_data:UserToken,chat_name:str,response:Response):
    auth=admin_auth_check(login=token_data.login,token=token_data.user_token)
    if auth==True:
        result=create_chat(login=token_data.login,chat=chat_name)
    else:
        result={'result':False,'message':"Доступно только администратору", 'category':"warning",'cod':401}
    response.status_code=result['cod']
    del result['cod']
    return result