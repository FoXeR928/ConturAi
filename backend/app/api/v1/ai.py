from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.core.exceptions import AppError
from app.db.models import User
from app.db.session import get_session
from app.rag import add_document
from app.schemas import TextAdd, MessageIn
from app.services import ai_service, parser

router = APIRouter()


@router.post("/messages/create")
async def create_ai_message(
    chat_id: int,
    payload: MessageIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    answer = await ai_service.ask(session, user, chat_id, payload.text)
    return {
        "result": True,
        "answer": answer,
        "message": "Ответ создан",
        "category": "success",
    }


@router.post("/docs/read")
async def read_doc(
    doc: UploadFile,
    _: User = Depends(get_admin_user),
):
    MAX_SIZE = 20 * 1024 * 1024
    if doc.size and doc.size > MAX_SIZE:
        raise AppError("Файл слишком большой (максимум 20 МБ)", "warning", 413)
        
    data = await doc.read()
    text = parser.parse_file(doc.content_type or "", data)
    if text is None:
        raise AppError("Формат не поддерживается", "warning", 415)
    
    return {
        "result": True,
        "file_name": doc.filename,
        "file_text": text,
        "message": "Текст получен",
        "category": "success",
    }


@router.post("/docs/create")
async def create_doc(
    payload: TextAdd,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    count = await add_document(session, payload.name, payload.text)
    return {
        "result": True,
        "message": f"Документ загружен ({count} чанков)",
        "category": "success",
    }