from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models import Tag

# ==============================================================================
# БЛОК 1: ПОЛУЧЕНИЕ СПИСКА ТЕГОВ
# ==============================================================================

async def list_tags(session: AsyncSession) -> list[dict]:
    """
    Возвращает список всех тегов из базы данных, отсортированных по алфавиту.
    
    Используется как для отрисовки списка в админ-панели, так и для 
    выпадающего меню выбора тегов в интерфейсе чата.
    Возвращает список словарей (вместо ORM-объектов), чтобы фронтенду 
    было проще работать с JSON.
    """
    result = await session.execute(select(Tag).order_by(Tag.name))
    return [
        {"id": str(t.id), "name": t.name, "color": t.color} 
        for t in result.scalars().all()
    ]


# ==============================================================================
# БЛОК 2: СОЗДАНИЕ НОВОГО ТЕГА
# ==============================================================================

async def create_tag(session: AsyncSession, name: str, color: str) -> None:
    """
    Создает новый тег в справочнике.
    
    Защита от дубликатов:
    Перед созданием проверяет, нет ли уже тега с таким же названием. 
    Если есть — выбрасывает ошибку 409 (Conflict).
    Это защищает базу от появления двух "Бухгалтерий" с разными цветами.
    """
    # Проверка на существование тега с таким же именем
    exists = (
        await session.execute(select(Tag).where(Tag.name == name))
    ).scalar_one_or_none()
    
    if exists:
        raise AppError("Тег с таким названием уже существует", "warning", 409)

    # Создаем и сохраняем новый тег
    tag = Tag(name=name, color=color)
    session.add(tag)
    await session.commit()


# ==============================================================================
# БЛОК 3: УДАЛЕНИЕ ТЕГА
# ==============================================================================

async def delete_tag(session: AsyncSession, tag_id: UUID) -> None:
    """
    Удаляет тег из справочника по его UUID.
    
    Примечание: на текущий момент теги в документах хранятся как массив строк (JSONB).
    При удалении тега из справочника, в самих документах он остается. 
    В будущем здесь можно добавить логику "зачистки" (удаления этого тега 
    из всех записей в таблице Upload), чтобы не оставалось "мусорных" тегов.
    """
    await session.execute(delete(Tag).where(Tag.id == tag_id))
    await session.commit()