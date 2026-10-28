from uuid import UUID
from pathlib import Path
import shutil

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.config import settings
from app.db.models import Upload, User, Document
from app.services import file_storage

# ==============================================================================
# БЛОК 1: СОЗДАНИЕ ЗАГРУЗКИ (СОХРАНЕНИЕ ФАЙЛА И ЗАПИСИ В БД)
# ==============================================================================

async def create_upload(
    session: AsyncSession,
    user: User,
    original_name: str,
    mime_type: str | None,
    data: bytes | None,
    parsed_text: str,
    tags: list[str] | None = None,
) -> Upload:
    """
    Создает запись о загруженном документе.
    
    Если передан `data` (файл), он сохраняется на диск. 
    Если `data` = None (документ создан из вставленного текста), 
    то сохраняется только текст.
    
    Возвращает объект Upload с заполненным ID, чтобы API мог отдать его фронтенду.
    """
    stored_name = None
    size = 0
    
    if data is not None:
        # --- ЗАЩИТА ОТ ПЕРЕПОЛНЕНИЯ ДИСКА ---
        # Перед сохранением файла проверяем, хватит ли места.
        data_dir = Path(settings.data_dir)
        if data_dir.exists():
            free_space = shutil.disk_usage(data_dir).free
            # Требуем, чтобы после сохранения осталось минимум 500 МБ свободного места
            if free_space < (len(data) + 500 * 1024 * 1024):
                raise AppError("Недостаточно места на диске для сохранения файла", "error", 507)

        # Сохраняем физический файл на диск (возвращает сгенерированное имя)
        stored_name = file_storage.save_original(data, original_name)
        size = len(data)
        
    # Создаем запись в базе данных
    upload = Upload(
        original_name=original_name,
        stored_name=stored_name,
        mime_type=mime_type,
        size=size,
        text=parsed_text,
        uploaded_by=user.login,
        tags=tags or [], # Если теги не переданы, сохраняем пустой массив
    )
    session.add(upload)
    await session.commit()
    
    # Обновляем объект, чтобы получить сгенерированные БД поля (например, created_at и id)
    await session.refresh(upload)
    return upload


# ==============================================================================
# БЛОК 2: ПРОСМОТР СПИСКА ДОКУМЕНТОВ (С ПАГИНАЦИЕЙ)
# ==============================================================================

async def list_uploads(session: AsyncSession, limit: int = 50, offset: int = 0) -> list[dict]:
    """
    Возвращает список загруженных документов для админ-панели.
    
    Использует пагинацию (limit, offset), чтобы не выгружать тысячи записей 
    за один раз, если документов очень много.
    Возвращает список словарей (вместо ORM-объектов) для удобства сериализации в JSON.
    """
    rows = (
        await session.execute(
            select(
                Upload.id,
                Upload.original_name,
                Upload.mime_type,
                Upload.size,
                Upload.chunks_count,
                Upload.uploaded_by,
                Upload.created_at,
                Upload.tags,
            )
            .order_by(Upload.created_at.desc()) # Сначала новые
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [dict(r._mapping) for r in rows]


# ==============================================================================
# БЛОК 3: ПОЛУЧЕНИЕ КОНКРЕТНОГО ДОКУМЕНТА
# ==============================================================================

async def get_upload(session: AsyncSession, upload_id: UUID) -> Upload:
    """
    Вспомогательная функция: находит документ по ID или выбрасывает ошибку 404.
    Используется в других методах (например, при скачивании или удалении).
    """
    upload = (
        await session.execute(select(Upload).where(Upload.id == upload_id))
    ).scalar_one_or_none()
    if not upload:
        raise AppError("Документ не найден", "warning", 404)
    return upload


# ==============================================================================
# БЛОК 4: УДАЛЕНИЕ ДОКУМЕНТА (ПОЛНАЯ ОЧИСТКА)
# ==============================================================================

async def delete_upload(session: AsyncSession, upload_id: UUID) -> None:
    """
    Удаляет документ полностью из системы.
    
    Состоит из трех шагов:
    1. Удаление физического файла с диска.
    2. Удаление всех чанков (векторов) из RAG-базы.
    3. Удаление самой записи из таблицы Upload.
    
    Явное удаление чанков (Document) добавлено для надежности, 
    чтобы не полагаться только на ON DELETE CASCADE в базе данных.
    """
    upload = await get_upload(session, upload_id)
    
    # 1. Удаляем файл с диска (если он есть)
    file_storage.delete_file(upload.stored_name)
    
    # 2. Явно чистим документы (чанки), чтобы не оставались "сироты"
    await session.execute(
        delete(Document).where(Document.upload_id == upload_id)
    )
    
    # 3. Удаляем саму запись о загрузке
    await session.execute(delete(Upload).where(Upload.id == upload_id))
    await session.commit()


# ==============================================================================
# БЛОК 5: ОБНОВЛЕНИЕ СТАТИСТИКИ ЧАНКОВ
# ==============================================================================

async def set_chunks_count(
    session: AsyncSession, upload_id: UUID, count: int
) -> None:
    """
    Обновляет поле chunks_count у документа.
    
    Вызывается после того, как RAG-модуль разбил текст на чанки 
    и сохранил их в базу. Нужно для отображения статистики в админке.
    """
    upload = await get_upload(session, upload_id)
    upload.chunks_count = count
    await session.commit()