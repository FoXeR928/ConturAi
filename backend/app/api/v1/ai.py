from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user, get_editor_user
from app.core.exceptions import AppError
from app.db.models import User
from app.db.session import get_session
from app.rag import add_document
from app.schemas import TextAdd, MessageIn
from app.services import (
    ai_service, 
    file_storage, 
    parser, 
    upload_service, 
    download_service, 
    audit_service, 
    llm_config_service
)

router = APIRouter()

# ==============================================================================
# БЛОК 1: ГЕНЕРАЦИЯ ОТВЕТОВ ИИ (ЧАТ)
# ==============================================================================

@router.post("/messages/create")
async def create_ai_message(
    chat_id: UUID,
    payload: MessageIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Основной эндпоинт для отправки сообщения в чат.
    Автоматически определяет, как отдавать ответ (стримом или целиком) 
    на основе глобальных настроек в БД.
    """
    # Читаем настройки LLM из базы данных
    raw_configs = await llm_config_service.get_all(session)
    is_stream = raw_configs.get("vllm_stream", "false").lower() == "true"

    if is_stream:
        # Если в БД включен стриминг, возвращаем поток (SSE)
        return await ai_service.ask_stream(session, user, chat_id, payload.text, tags=payload.tags)
    
    # Если стриминг выключен, генерируем ответ целиком и отдаем обычный JSON
    answer = await ai_service.ask(session, user, chat_id, payload.text, tags=payload.tags) 
    return {
        "result": True,
        "answer": answer,
        "sources": sources,
        "message": "Ответ создан",
        "category": "success",
    }

@router.post("/messages/stream")
async def create_ai_message_stream(
    chat_id: UUID,
    payload: MessageIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Принудительный стриминг.
    Используется фронтендом, когда пользователь явно включил тумблер "Стриминг ответа" 
    в интерфейсе чата (переопределяет настройку из БД).
    """
    return await ai_service.ask_stream(session, user, chat_id, payload.text, tags=payload.tags)


# ==============================================================================
# БЛОК 2: РАБОТА С ДОКУМЕНТАМИ (ЗАГРУЗКА И ПАРСИНГ)
# ==============================================================================

@router.post("/docs/read")
async def read_doc(
    request: Request,
    doc: UploadFile,
    user: User = Depends(get_editor_user), # Доступно админам и редакторам
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для загрузки файла и извлечения из него текста.
    Файл сохраняется на диск (оригинал), а текст парсится для дальнейшей индексации.
    """
    # 1. Проверка размера (не более 20 МБ)
    MAX_SIZE = 20 * 1024 * 1024
    if doc.size and doc.size > MAX_SIZE:
        raise AppError("Файл слишком большой (максимум 20 МБ)", "warning", 413)

    # 2. Чтение файла и проверка на пустоту
    data = await doc.read()
    if not data:
        raise AppError("Файл пустой", "warning", 400)
        
    # 3. Логирование действия в аудит (кто и что загрузил)
    await audit_service.log_action(
        session, user.login, "upload_doc", 
        details=f"Загружен файл: {doc.filename}", ip_address=request.client.host
    )
    
    # 4. Парсинг файла (извлечение текста и таблиц)
    text = parser.parse_file(
        doc.content_type or "",
        data,
        filename=doc.filename or "",
    )
    if text is None:
        raise AppError(
            f"Формат не поддерживается. Поддерживаются: PDF, DOCX, XLSX, TXT, MD",
            "warning",
            415,
        )

    # 5. Сохранение оригинала на диск и записи о загрузке в БД
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
        "file_text": upload.text, # Возвращаем распарсенный текст на фронт для предпросмотра
        "message": "Текст получен, оригинал сохранён",
        "category": "success",
    }


@router.post("/docs/create")
async def create_doc(
    payload: TextAdd,
    user: User = Depends(get_editor_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Эндпоинт для индексации документа в RAG (векторную БД).
    Может принимать либо ID ранее загруженного файла (upload_id), 
    либо просто текст (если текст вводился вручную).
    """
    upload_id = payload.upload_id
    
    if upload_id is not None:
        # Сценарий А: текст берется из уже загруженного файла
        upload = await upload_service.get_upload(session, upload_id)
        text_for_chunks = payload.text or upload.text
        source_name = payload.name or upload.original_name
        
        # Если при создании указали теги, обновляем их у загрузки
        if payload.tags:
            upload.tags = payload.tags
            await session.commit()
    else:
        # Сценарий Б: создаем документ "с нуля" только из текста (без файла)
        upload = await upload_service.create_upload(
            session=session,
            user=user,
            original_name=payload.name,
            mime_type=None,
            data=None,
            parsed_text=payload.text,
            tags=payload.tags,
        )
        upload_id = upload.id
        text_for_chunks = payload.text
        source_name = payload.name

    # Нарезаем текст на чанки и генерируем вектора (сохраняется в pgvector)
    count = await add_document(
        session,
        source=source_name,
        text=text_for_chunks,
        upload_id=upload_id,
    )
    
    # Обновляем счетчик чанков в БД, чтобы отображать в админке
    await upload_service.set_chunks_count(session, upload_id, count)

    return {
        "result": True,
        "upload_id": str(upload_id),
        "message": f"Документ загружен ({count} чанков)",
        "category": "success",
    }


# ==============================================================================
# БЛОК 3: УПРАВЛЕНИЕ ДОКУМЕНТАМИ (СПИСОК, СКАЧИВАНИЕ, УДАЛЕНИЕ)
# ==============================================================================

@router.get("/docs/list")
async def list_docs(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
    offset: int = 0,
):
    """
    Получение списка всех загруженных документов (с пагинацией).
    Доступно только администраторам.
    """
    return {
        "result": True,
        "uploads": await upload_service.list_uploads(session, limit, offset),
        "message": "Документы получены",
        "category": "success",
    }


@router.get("/docs/tags")
async def list_tags(
    _: User = Depends(get_editor_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Собирает все уникальные теги из загруженных документов.
    (Примечание: в будущем лучше перевести на таблицу Tag, которую наполняет админ).
    """
    from sqlalchemy import select
    from app.db.models import Upload
    uploads = (await session.execute(select(Upload.tags))).scalars().all()
    tags = set()
    for tag_list in uploads:
        if tag_list:
            tags.update(tag_list)
    return {"result": True, "tags": sorted(list(tags))}


@router.get("/docs/{upload_id}/download")
async def download_doc(
    upload_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Скачивание оригинального файла (PDF/DOCX) из хранилища.
    Проверяет права пользователя (через download_service).
    """
    upload = await upload_service.get_upload(session, upload_id)
    
    # Проверяем, есть ли физический файл (может быть текстовый документ без файла)
    if not upload.stored_name:
        raise AppError("У этого документа нет оригинала", "warning", 404)
    
    # Проверка прав доступа (может ли этот юзер скачивать этот файл)
    has_access = await download_service.check_access(session, user, upload_id)
    if not has_access:
        raise AppError("Скачивание запрещено. Запросите доступ у администратора.", "warning", 403)

    # Формируем путь и отдаем файл
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
    user: User = Depends(get_editor_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Полное удаление документа: физический файл с диска, 
    запись из БД (uploads) и все связанные чанки из RAG (documents).
    """
    # Вызываем сервис удаления (он чистит и диск, и БД)
    await upload_service.delete_upload(session, upload_id)
    
    # Логируем действие
    await audit_service.log_action(
        session, user.login, "delete_doc", details=f"Удален ID: {upload_id}"
    )
    
    return {
        "result": True,
        "message": "Документ удалён",
        "category": "success",
    }