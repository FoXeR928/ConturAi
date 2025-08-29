from fastapi import APIRouter, Response, Depends
from pydantic import BaseModel
from typing import List

from api.api_auth import User, get_current_user
from db_modules.db_query_chat import (
    create_chat_query,
    get_chats_query,
    get_messages_chat_query,
    create_message_query,
    delet_chat_query,
    get_delet_chats_query,
    delet_chats_irrevocably_list_query,
    delet_chats_irrevocably_all_list,
    recovery_chats_list_query,
    delete_message_query,
)

chat_app = APIRouter(prefix="/chats", tags=["Чаты"])


class Message(BaseModel):
    text: str


@chat_app.post("/create", summary="Создание чата")
async def create_chat_api(
    chat_name: str, response: Response, current_user: User = Depends(get_current_user)
):
    result = create_chat_query(login=current_user.login, chat=chat_name)
    response.status_code = result["cod"]
    del result["cod"]
    return result


@chat_app.get("/get", summary="Получение чатов")
async def get_chats_api(
    response: Response, current_user: User = Depends(get_current_user)
):
    result = get_chats_query(login=current_user.login)
    response.status_code = result["cod"]
    del result["cod"]
    return result


@chat_app.get("/messages/get", summary="Получение сообщений чата")
async def get_messages_api(
    response: Response, chat_id: int, current_user: User = Depends(get_current_user)
):
    result = get_messages_chat_query(login=current_user.login, chat_id=chat_id)
    response.status_code = result["cod"]
    del result["cod"]
    return result


@chat_app.post("/messages/create", summary="Создание сообщения")
async def create_message_api(
    response: Response,
    chat_id: int,
    message: Message,
    current_user: User = Depends(get_current_user),
):
    result = create_message_query(
        login=current_user.login, chat_id=chat_id, text=message.text
    )
    response.status_code = result["cod"]
    del result["cod"]
    return result


@chat_app.delete("/messages/delet", summary="Удаление сообщения")
async def create_message_api(
    response: Response,
    chat_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
):
    result = delete_message_query(
        user=current_user, chat_id=chat_id, message_id=message_id
    )
    response.status_code = result["cod"]
    del result["cod"]
    return result


@chat_app.patch("/delet", summary="Удаление чата")
async def delet_chat_api(
    response: Response, chat_id: int, current_user: User = Depends(get_current_user)
):
    result = delet_chat_query(user=current_user, chat_id=chat_id)
    response.status_code = result["cod"]
    del result["cod"]
    return result


@chat_app.get(
    "/delet/irrevocably/get", summary="Получение чатов на безвозвратное удаление"
)
async def get_delet_chats_api(
    response: Response, current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = get_delet_chats_query()
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


@chat_app.delete(
    "/delet/irrevocably/list", summary="Удаление безвозвратно списка чатов"
)
async def delet_chats_irrevocably_list_api(
    response: Response, chats: List[int], current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = delet_chats_irrevocably_list_query(chats=chats)
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


@chat_app.delete("/delet/irrevocably/all", summary="Удаление безвозвратно всех чатов")
async def delet_chats_irrevocably_list_api(
    response: Response, current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = delet_chats_irrevocably_all_list()
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


@chat_app.patch("/recovery/list", summary="Восстановление списка чатов")
async def recovery_chats_list_api(
    response: Response, chats: List[int], current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = recovery_chats_list_query(chats=chats)
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
