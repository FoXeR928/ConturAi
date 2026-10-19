import argparse
import asyncio
import secrets
import string
from pathlib import Path

from loguru import logger
from sqlalchemy import select, text

from app.core.config import (
    ADMIN_LOGIN,
    ADMIN_NAME,
    SYSTEM_CHAT_ROLE,
    SYSTEM_LOGIN,
    settings,
)
from app.core.logging import setup_logging
from app.core.secrets import load_or_create_jwt_key
from app.db.models import Base, Prompt, User
from app.db.session import async_session_factory, engine
from app.services.prompt_service import DEFAULT_PROMPTS

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
ENV_EXAMPLE = Path(__file__).resolve().parent.parent / ".env.example"


# --- Команда: Инициализация БД ---
async def _create_schema() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Схема базы данных создана")


async def _seed_prompts(session) -> None:
    for key, meta in DEFAULT_PROMPTS.items():
        exists = (
            await session.execute(select(Prompt).where(Prompt.key == key))
        ).scalar_one_or_none()
        if exists is None:
            session.add(
                Prompt(key=key, value=meta["value"], description=meta["description"])
            )
    await session.commit()
    logger.info("Промты по умолчанию добавлены")


async def cmd_init_db() -> None:
    setup_logging()
    load_or_create_jwt_key()
    logger.info("Инициализация БД...")
    await _create_schema()
    async with async_session_factory() as session:
        await _seed_prompts(session)
    logger.success("Инициализация БД завершена")


# --- Команда: Сброс/Создание админа ---
async def cmd_reset_admin() -> None:
    setup_logging()
    async with async_session_factory() as session:
        password = secrets.token_urlsafe(16)

        admin = (
            await session.execute(select(User).where(User.login == ADMIN_LOGIN))
        ).scalar_one_or_none()

        if admin:
            admin.set_password(password)
            admin.is_admin = True
            admin.disabled = False
            logger.warning(f"Пароль администратора '{ADMIN_LOGIN}' сброшен.")
        else:
            admin = User(login=ADMIN_LOGIN, user_name=ADMIN_NAME, is_admin=True)
            admin.set_password(password)
            session.add(admin)
            logger.warning(f"Администратор '{ADMIN_LOGIN}' создан.")

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

        await session.commit()

        logger.warning("=" * 72)
        logger.warning("  ДАННЫЕ ДЛЯ ВХОДА")
        logger.warning(f"  Логин:  {ADMIN_LOGIN}")
        logger.warning(f"  Пароль: {password}")
        logger.warning("  Пароль показывается один раз — сохраните его!")
        logger.warning("=" * 72)


# --- Команда: Генерация .env (для локального запуска без Docker) ---
def _generate_password(length=32) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def cmd_setup_env() -> None:
    if ENV_FILE.exists():
        logger.info(f"Файл {ENV_FILE} уже существует. Пропускаем генерацию.")
        return

    if not ENV_EXAMPLE.exists():
        logger.error(f"Не найден {ENV_EXAMPLE}")
        return

    logger.info("Генерация паролей и создание .env")
    db_user = "conturai_user"
    db_password = _generate_password(32)

    content = ENV_EXAMPLE.read_text(encoding="utf-8")
    content = content.replace("DB_USER=conturai", f"DB_USER={db_user}")
    content = content.replace("DB_PASSWORD=conturai", f"DB_PASSWORD={db_password}")

    ENV_FILE.write_text(content, encoding="utf-8")
    
    logger.success(f"Создан файл {ENV_FILE}")
    logger.warning(f"👤 Пользователь БД: {db_user}")
    logger.warning(f"🔑 Пароль БД:       {db_password}")


# --- CLI ---
def main() -> None:
    parser = argparse.ArgumentParser(description="ConturAI management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Создать таблицы и промты")
    subparsers.add_parser("reset-admin", help="Сбросить пароль админа")
    subparsers.add_parser("setup-env", help="Сгенерировать .env файл")

    args = parser.parse_args()

    if args.command == "init-db":
        asyncio.run(cmd_init_db())
    elif args.command == "reset-admin":
        asyncio.run(cmd_reset_admin())
    elif args.command == "setup-env":
        cmd_setup_env()

if __name__ == "__main__":
    main()