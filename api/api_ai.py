from fastapi import APIRouter, Response,Depends
from pydantic import BaseModel

from db_modules.db_query_ai import create_message_ai
from api.api_auth import User,get_current_user
from api.api_chat import Message

ai_app = APIRouter(prefix="/AI", tags=["Нейросеть"])

@ai_app.post("/messages/create_ai", summary="Создание сообщения AI")
async def get_chats_api(response: Response,chat_id:int,message:Message,current_user: User=Depends(get_current_user)):
    result = create_message_ai(login=current_user.login,chat_id=chat_id,text=message.text)
    response.status_code = result["cod"]
    del result["cod"]
    return result