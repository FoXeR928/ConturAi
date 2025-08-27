from fastapi import APIRouter, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional

from db_modules.db_query_auth import (
    auth_query,
    logout_query,
    get_token_query,
    create_token_query,
    decode_token,
    get_current_user_query,
)

auth_app = APIRouter(prefix="/auth", tags=["Авторизация"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    login: str
    name: Optional[str] = None
    role: str


class Auth(User):
    password: str
    disabled: bool = False


async def get_current_user(token: str = Depends(oauth2_scheme)):
    login = decode_token(token=token)
    user = get_current_user_query(login=login)
    return User(login=user[0], name=user[1], role=user[2])


@auth_app.post(
    "/login", response_model=Token, summary="Авторизация для получения токена"
)
async def login_api(response: Response, auth: OAuth2PasswordRequestForm = Depends()):
    result = auth_query(login=auth.username, password=auth.password)
    response.status_code = result["cod"]
    del result["cod"]
    return result


@auth_app.post("/logout", summary="Выход из учетной записи")
async def logout_api(
    response: Response, current_user: User = Depends(get_current_user)
):
    result = logout_query(login=current_user.login)
    response.status_code = result["cod"]
    del result["cod"]
    return result


@auth_app.get("/get_token", summary="Получени токена API")
async def get_token_api(
    response: Response, current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = get_token_query()
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 403,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result


@auth_app.put("/create_token", summary="Создание токена API")
async def create_token_api(
    response: Response, current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = create_token_query()
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 403,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result
