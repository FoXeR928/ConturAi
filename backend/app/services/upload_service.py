from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models import Upload, User
from app.services import file_storage


async def create_upload(
    session: AsyncSession,
    user: User,
    original_name: str,
    mime_type: str | None,
    data: bytes | None,
    parsed_text: str,
) -> Upload:
    stored_name = None
    size = 0
    if data is not None:
        stored_name = file_storage.save_original(data, original_name)
        size = len(data)

    upload = Upload(
        original_name=original_name,
        stored_name=stored_name,
        mime_type=mime_type,
        size=size,
        text=parsed_text,
        uploaded_by=user.login,
    )
    session.add(upload)
    await session.commit()
    await session.refresh(upload)
    return upload


async def list_uploads(session: AsyncSession) -> list[dict]:
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
            ).order_by(Upload.created_at.desc())
        )
    ).all()
    return [dict(r._mapping) for r in rows]


async def get_upload(session: AsyncSession, upload_id: UUID) -> Upload:
    upload = (
        await session.execute(select(Upload).where(Upload.id == upload_id))
    ).scalar_one_or_none()
    if not upload:
        raise AppError("Документ не найден", "warning", 404)
    return upload


async def delete_upload(session: AsyncSession, upload_id: UUID) -> None:
    upload = await get_upload(session, upload_id)
    file_storage.delete_file(upload.stored_name)
    await session.execute(delete(Upload).where(Upload.id == upload_id))
    await session.commit()


async def set_chunks_count(
    session: AsyncSession, upload_id: UUID, count: int
) -> None:
    upload = await get_upload(session, upload_id)
    upload.chunks_count = count
    await session.commit()