from fastapi import APIRouter, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import jwt

from db_modules.db_query import admin_auth_check, user_auth_check
from db_modules.db_query_auth import (
    auth_query,
    logout_query,
    get_token_query,
    create_token_query,
)

auth_app = APIRouter(prefix="/auth", tags=["Авторизация"])

class Auth(BaseModel):
    password: str
    disabled: bool=False

class Token(BaseModel):
    access_token:str
    token_type:str

class User(BaseModel):
    login: str
    name: Optional[str] = None

def get_current_user(current_user:User=Depends()):


@auth_app.post("/", response_model=Token, summary="Авторизация для получения токена")
async def auth_api(response: Response,auth: OAuth2PasswordRequestForm=Depends()):
    result = auth_query(login=auth.username, password=auth.password)
    response.status_code = result["cod"]
    del result["cod"]
    return result


@auth_app.post("/logout", summary="Выход из учетной записи")
async def auth_api(response: Response,current_user: User=Depends(get_current_user)):
    auth = user_auth_check(login=current_user.login)
    if auth == True:
        result = logout_query(login=current_user.login)
    else:
        result = {
            "result": False,
            "message": "Авторизация не пройдена",
            "category": "warning",
            "cod": 401,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@auth_app.get("/get_token", summary="Получени токена API")
async def get_token_api(response: Response, current_user: User=Depends(get_current_user),):
    auth = admin_auth_check(login=current_user.login)
    if auth == True:
        result = get_token_query()
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 401,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@auth_app.put("/create_token", summary="Создание токена API")
async def create_token_api(token_data: User, response: Response):
    auth = admin_auth_check(login=token_data.login)
    if auth == True:
        result = create_token_query()
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 401,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result
