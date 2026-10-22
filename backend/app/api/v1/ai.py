from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.core.exceptions import AppError
from app.db.models import User
from app.db.session import get_session
from app.rag import add_document
from app.schemas import TextAdd, MessageIn
from app.services import ai_service, file_storage, parser, upload_service

router = APIRouter()


@router.post("/messages/create")
async def create_ai_message(
    chat_id: UUID,
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


# ---------- Документы ----------

@router.post("/docs/read")
async def read_doc(
    doc: UploadFile,
    user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    MAX_SIZE = 20 * 1024 * 1024
    if doc.size and doc.size > MAX_SIZE:
        raise AppError("Файл слишком большой (максимум 20 МБ)", "warning", 413)

    data = await doc.read()
    text = parser.parse_file(doc.content_type or "", data)
    if text is None:
        raise AppError("Формат не поддерживается", "warning", 415)

    upload = await upload_service.create_upload(
        session=session,
        user=user,
        original_name=doc.filename or "upload.bin",
        mime_type=doc.content_type,
        data=data,
        parsed_text=text,
    )

    return {
        "result": True,
        "upload_id": str(upload.id),
        "file_name": upload.original_name,
        "file_text": upload.text,
        "message": "Текст получен, оригинал сохранён",
        "category": "success",
    }


@router.post("/docs/create")
async def create_doc(
    payload: TextAdd,
    user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    upload_id = payload.upload_id
    if upload_id is not None:
        upload = await upload_service.get_upload(session, upload_id)
        text_for_chunks = payload.text or upload.text
        source_name = payload.name or upload.original_name
    else:
        # текст без файла
        upload = await upload_service.create_upload(
            session=session,
            user=user,
            original_name=payload.name,
            mime_type=None,
            data=None,
            parsed_text=payload.text,
        )
        upload_id = upload.id
        text_for_chunks = payload.text
        source_name = payload.name

    count = await add_document(
        session,
        source=source_name,
        text=text_for_chunks,
        upload_id=upload_id,
    )
    await upload_service.set_chunks_count(session, upload_id, count)

    return {
        "result": True,
        "upload_id": str(upload_id),
        "message": f"Документ загружен ({count} чанков)",
        "category": "success",
    }


@router.get("/docs/list")
async def list_docs(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    return {
        "result": True,
        "uploads": await upload_service.list_uploads(session),
        "message": "Документы получены",
        "category": "success",
    }


@router.get("/docs/{upload_id}/download")
async def download_doc(
    upload_id: UUID,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    upload = await upload_service.get_upload(session, upload_id)
    if not upload.stored_name:
        raise AppError("У этого документа нет оригинала", "warning", 404)
    path = file_storage.path_of(upload.stored_name)
    if not path.exists():
        raise AppError("Файл не найден на диске", "error", 500)
    return FileResponse(
        path=str(path),
        media_type=upload.mime_type or "application/octet-stream",
        filename=upload.original_name,
    )


@router.delete("/docs/{upload_id}")
async def delete_doc(
    upload_id: UUID,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    await upload_service.delete_upload(session, upload_id)
    return {
        "result": True,
        "message": "Документ удалён",
        "category": "success",
    }