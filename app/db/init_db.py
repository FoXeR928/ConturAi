from sqlalchemy import select, text

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.models import ApiToken, Base, User
from app.db.session import async_session_factory, engine
from app.rag.embeddings import get_embedding_dim
from loguru import logger


async def _create_schema() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)


async def _seed_admin() -> None:
    """Создаёт администратора, если его ещё нет."""
    async with async_session_factory() as session:
        admin = (
            await session.execute(
                select(User).where(User.login == settings.default_admin_login)
            )
        ).scalar_one_or_none()

        if admin is not None:
            logger.debug("Администратор уже существует")
            return

        admin = User(
            login=settings.default_admin_login,
            user_name=settings.default_admin_name,
            is_admin=True,
        )
        admin.set_password(settings.default_admin_password)
        session.add(admin)

        # системный пользователь нужен для записи ответов нейросети
        system = (
            await session.execute(
                select(User).where(User.login == settings.system_login)
            )
        ).scalar_one_or_none()
        if system is None:
            session.add(
                User(
                    login=settings.system_login,
                    is_system=True,
                    chat_role="assistant",
                )
            )

        # пустая строка для API-токена
        token_row = (
            await session.execute(select(ApiToken).where(ApiToken.id == 1))
        ).scalar_one_or_none()
        if token_row is None:
            session.add(ApiToken(id=1, token=None))

        await session.commit()
        logger.success(
            f"Создан администратор '{settings.default_admin_login}'"
        )


async def init_db() -> None:
    setup_logging()
    get_embedding_dim()  # прогрев модели + проверка размерности

    if settings.auto_create_schema:
        await _create_schema()

    await _seed_admin()
    logger.info("Database initialized")