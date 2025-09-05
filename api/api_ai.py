from fastapi import APIRouter, Response, Depends, UploadFile
from pydantic import BaseModel

from db_modules.db_query_ai import create_message_ai_query
from api.api_auth import User, get_current_user
from api.api_chats import Message
from ai_modules.parther import check_file_type
from ai_modules.query_rag_db import add_docs_rquery

ai_app = APIRouter(prefix="/AI", tags=["Нейросеть"])


class TextAdd(BaseModel):
    name: str
    text: str


@ai_app.post("/messages/create_ai", summary="Создание сообщения AI")
async def create_message_ai_api(
    response: Response,
    chat_id: int,
    message: Message,
    current_user: User = Depends(get_current_user),
):
    result = create_message_ai_query(
        login=current_user.login, chat_id=chat_id, text=message.text
    )
    response.status_code = result["cod"]
    del result["cod"]
    return result


@ai_app.post("/docs/read", summary="Загрузка документа для чтения")
async def read_doc_api(
    response: Response,
    doc: UploadFile,
    current_user: User = Depends(get_current_user),
):
    if current_user.isAdmin == True:
        file_name = doc.filename
        file_type = doc.content_type
        file_dytes = doc.file
        text = check_file_type(file_type=file_type, file_dytes=file_dytes)
        result = {
            "result": True,
            "file_name": file_name,
            "file_text": text,
            "message": "Текст получен",
            "category": "success",
            "cod": 200,
        }
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


@ai_app.post("/docs/create", summary="Загрузка документа в RAG базу")
async def read_doc_api(
    response: Response,
    doc_add: TextAdd,
    current_user: User = Depends(get_current_user),
):
    if current_user.isAdmin == True:
        result = add_docs_rquery(doc_name=doc_add.name, doc_text=doc_add.text)
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
