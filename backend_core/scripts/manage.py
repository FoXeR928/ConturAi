import argparse
import asyncio
import secrets

from loguru import logger
from sqlalchemy import select, text

from app.core.config import (
    ADMIN_LOGIN,
    ADMIN_NAME,
    SYSTEM_CHAT_ROLE,
    SYSTEM_LOGIN,
)
from app.core.logging import setup_logging
from app.core.secrets import load_or_create_jwt_key
from app.db.models import Base, User
from app.db.session import async_session_factory, engine

# ==============================================================================
# БЛОК 1: ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ (INIT-DB)
# ==============================================================================

async def _create_schema() -> None:
    """Создает все таблицы ядра."""
    async with engine.begin() as conn:
        # Плагин RAG сам добавит CREATE EXTENSION vector, если ему это понадобится.
        # Ядру это не нужно.
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Схема базы данных создана")

async def cmd_init_db() -> None:
    """Создает таблицы, администратора и системного пользователя."""
    setup_logging()
    load_or_create_jwt_key()
    logger.info("Инициализация БД...")
    
    await _create_schema()
    
    async with async_session_factory() as session:
        # Создаем администратора
        admin = (await session.execute(select(User).where(User.login == ADMIN_LOGIN))).scalar_one_or_none()
        if not admin:
            password = secrets.token_urlsafe(16)
            admin = User(login=ADMIN_LOGIN, user_name=ADMIN_NAME, role="admin")
            admin.set_password(password)
            session.add(admin)
            logger.warning("=" * 72)
            logger.warning(f"  Создан администратор: {ADMIN_LOGIN}")
            logger.warning(f"  Пароль: {password}")
            logger.warning("  Пароль показывается один раз — сохраните его!")
            logger.warning("=" * 72)
        else:
            logger.info(f"Администратор '{ADMIN_LOGIN}' уже существует.")

        # Создаем системного пользователя (от его имени LLM пишет ответы)
        system = (await session.execute(select(User).where(User.login == SYSTEM_LOGIN))).scalar_one_or_none()
        if system is None:
            session.add(User(login=SYSTEM_LOGIN, is_system=True, chat_role=SYSTEM_CHAT_ROLE))
            logger.info(f"Создан системный пользователь '{SYSTEM_LOGIN}'.")

        await session.commit()
        
    logger.success("Инициализация БД завершена")


# ==============================================================================
# БЛОК 2: МИГРАЦИИ (ДЛЯ БУДУЩИХ ОБНОВЛЕНИЙ ЯДРА)
# ==============================================================================

async def cmd_migrate() -> None:
    setup_logging()
    logger.info("Применение миграций ядра...")

    # Метод create_all безопасно создает только те таблицы, которых нет.
    # Если вы добавляете новые колонки в ядро, здесь можно прописать ALTER TABLE.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Схема ядра проверена (новые таблицы созданы).")

    logger.success("Миграция ядра завершена.")


# ==============================================================================
# БЛОК 3: УПРАВЛЕНИЕ АДМИНИСТРАТОРОМ (RESET-ADMIN)
# ==============================================================================

async def cmd_reset_admin() -> None:
    """Сбрасывает пароль администратора на случайный."""
    setup_logging()
    async with async_session_factory() as session:
        password = secrets.token_urlsafe(16)
        admin = (await session.execute(select(User).where(User.login == ADMIN_LOGIN))).scalar_one_or_none()
        
        if admin:
            admin.set_password(password)
            admin.role = "admin"
            admin.disabled = False
            logger.warning(f"Пароль администратора '{ADMIN_LOGIN}' сброшен.")
        else:
            admin = User(login=ADMIN_LOGIN, user_name=ADMIN_NAME, role="admin")
            admin.set_password(password)
            session.add(admin)
            logger.warning(f"Администратор '{ADMIN_LOGIN}' создан.")

        # Гарантируем наличие системного пользователя
        system = (await session.execute(select(User).where(User.login == SYSTEM_LOGIN))).scalar_one_or_none()
        if system is None:
            session.add(User(login=SYSTEM_LOGIN, is_system=True, chat_role=SYSTEM_CHAT_ROLE))
        await session.commit()

        logger.warning("=" * 72)
        logger.warning("  ДАННЫЕ ДЛЯ ВХОДА")
        logger.warning(f"  Логин:  {ADMIN_LOGIN}")
        logger.warning(f"  Пароль: {password}")
        logger.warning("=" * 72)


# ==============================================================================
# БЛОК 4: CLI ИНТЕРФЕЙС (ARGPARSE)
# ==============================================================================

def main() -> None:
    """Главная точка входа для CLI ядра."""
    parser = argparse.ArgumentParser(description="ConturAI Core management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Создать таблицы, админа и системного пользователя")
    subparsers.add_parser("reset-admin", help="Сбросить пароль админа")
    subparsers.add_parser("migrate", help="Применить миграции таблиц ядра")

    args = parser.parse_args()

    if args.command == "init-db":
        asyncio.run(cmd_init_db())
    elif args.command == "reset-admin":
        asyncio.run(cmd_reset_admin())
    elif args.command == "migrate":
        asyncio.run(cmd_migrate())

if __name__ == "__main__":
    main()