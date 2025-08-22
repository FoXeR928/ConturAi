from fastapi import APIRouter, Response, Depends
from pydantic import BaseModel

from db_modules.db_query import admin_auth_check, user_auth_check, check_user
from db_modules.db_query_chat import create_chat, get_chats

chat_app = APIRouter(prefix="/chats", tags=["Чаты"])


class UserToken(BaseModel):
    login: str
    user_token: str


@chat_app.post("/create", summary="Создание чата")
async def create_chat_api(token_data: UserToken, chat_name: str, response: Response):
    auth = user_auth_check(login=token_data.login, token=token_data.user_token)
    if auth == True:
        result = create_chat(login=token_data.login, chat=chat_name)
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


@chat_app.get("/get", summary="Получение чатов")
async def get_chats_api(token_data: UserToken, response: Response):
    auth = user_auth_check(login=token_data.login, token=token_data.user_token)
    if auth == True:
        result = get_chats(login=token_data.login)
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
