from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Создаем асинхронный движок
engine = create_async_engine(
    settings.db_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Фабрика сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Генератор сессий для внедрения зависимостей (Depends) в FastAPI
async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session