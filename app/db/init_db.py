import secrets

from loguru import logger
from sqlalchemy import select, text

from app.core.config import settings
from app.core.constants import (
    ADMIN_LOGIN,
    ADMIN_NAME,
    SYSTEM_CHAT_ROLE,
    SYSTEM_LOGIN,
)
from app.core.logging import setup_logging
from app.core.secrets_store import load_or_create_jwt_key
from app.db.models import ApiToken, Base, User
from app.db.session import async_session_factory, engine
from app.rag.embeddings import get_embedding_dim


async def _create_schema() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)


def _generate_password() -> str:
    return secrets.token_urlsafe(16)


async def _seed_admin() -> None:
    async with async_session_factory() as session:
        admin = (
            await session.execute(select(User).where(User.login == ADMIN_LOGIN))
        ).scalar_one_or_none()

        if admin is not None:
            logger.debug(f"Администратор '{ADMIN_LOGIN}' уже существует")
            return

        password = _generate_password()

        admin = User(login=ADMIN_LOGIN, user_name=ADMIN_NAME, is_admin=True)
        admin.set_password(password)
        session.add(admin)

        system = (
            await session.execute(select(User).where(User.login == SYSTEM_LOGIN))
        ).scalar_one_or_none()
        if system is None:
            session.add(
                User(
                    login=SYSTEM_LOGIN,
                    is_system=True,
                    chat_role=SYSTEM_CHAT_ROLE,
                )
            )

        token_row = (
            await session.execute(select(ApiToken).where(ApiToken.id == 1))
        ).scalar_one_or_none()
        if token_row is None:
            session.add(ApiToken(id=1, token=None))

        await session.commit()

        logger.warning("=" * 72)
        logger.warning("  Создан администратор по умолчанию")
        logger.warning(f"  Логин:  {ADMIN_LOGIN}")
        logger.warning(f"  Пароль: {password}")
        logger.warning("  Пароль показывается один раз — сохраните его!")
        logger.warning("=" * 72)


async def init_db() -> None:
    setup_logging()
    load_or_create_jwt_key()   # гарантируем наличие ключа до первого запроса
    get_embedding_dim()

    if settings.auto_create_schema:
        await _create_schema()

    await _seed_admin()
    logger.info("Database initialized")