from fastapi import APIRouter, Response, Depends
from pydantic import BaseModel

from api.api_auth import User,get_current_user
from db_modules.db_query_chat import create_chat, get_chats,get_messages_chat,create_message

chat_app = APIRouter(prefix="/chats", tags=["Чаты"])

class Message(BaseModel):
    text: str

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

@chat_app.get("/messages", summary="Получение сообщений чата")
async def get_messages_api(response: Response,chat_id:int,current_user: User=Depends(get_current_user)):
    result = get_messages_chat(login=current_user.login,chat_id=chat_id)
    response.status_code = result["cod"]
    del result["cod"]
    return result

@chat_app.post("/messages/create", summary="Создание сообщения")
async def create_message_api(response: Response,chat_id:int,message:Message,current_user: User=Depends(get_current_user)):
    result = create_message(login=current_user.login,chat_id=chat_id,text=message.text)
    response.status_code = result["cod"]
    del result["cod"]
    return result