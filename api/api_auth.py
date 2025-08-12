from fastapi import APIRouter,Response
from pydantic import BaseModel

from db_modules.db_query_auth import auth_query

auth_app=APIRouter(prefix='/auth',tags=['Авторизация'])

class Auth(BaseModel):
    login:str
    password:str

@auth_app.post('/',summary='Авторизация для получения токена')
async def auth_api(auth_data:Auth,response:Response):
    db_query=auth_query(login=auth_data.login,password=auth_data.password)
    response.status_code=db_query['cod']
    del db_query['cod']
    return(db_query)
