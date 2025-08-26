from fastapi import APIRouter, Response, Depends
from pydantic import BaseModel

from api.api_auth import User,get_current_user
from db_modules.db_query_chat import create_chat, get_chats

chat_app = APIRouter(prefix="/chats", tags=["Чаты"])

@chat_app.post("/create", summary="Создание чата")
async def create_chat_api(chat_name: str, response: Response,current_user: User=Depends(get_current_user)):
    result = create_chat(login=current_user.login, chat=chat_name)
    response.status_code = result["cod"]
    del result["cod"]
    return result


@chat_app.get("/get", summary="Получение чатов")
async def get_chats_api(response: Response,current_user: User=Depends(get_current_user)):
    result = get_chats(login=current_user.login)
    response.status_code = result["cod"]
    del result["cod"]
    return result
