import argparse
import asyncio
import os
import secrets
import shutil
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
from app.services import llm_config_service
from app.services.prompt_service import DEFAULT_PROMPTS


# ---------------- DB ----------------

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
        await llm_config_service.seed_defaults(session)
    logger.success("Инициализация БД завершена")


# ---------------- Admin ----------------

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
                User(login=SYSTEM_LOGIN, is_system=True, chat_role=SYSTEM_CHAT_ROLE)
            )
        await session.commit()

        logger.warning("=" * 72)
        logger.warning("  ДАННЫЕ ДЛЯ ВХОДА")
        logger.warning(f"  Логин:  {ADMIN_LOGIN}")
        logger.warning(f"  Пароль: {password}")
        logger.warning("  Пароль показывается один раз — сохраните его!")
        logger.warning("=" * 72)


# ---------------- LLM ----------------

async def cmd_set_llm(args: argparse.Namespace) -> None:
    setup_logging()
    async with async_session_factory() as session:
        pairs = {
            "vllm_base_url": args.base_url,
            "vllm_api_key": args.api_key,
            "vllm_model_name": args.model,
            "vllm_temperature": args.temperature,
            "vllm_max_tokens": args.max_tokens,
        }
        for key, value in pairs.items():
            if value is None:
                continue
            await llm_config_service.update_config(session, key, str(value))
            logger.info(f"{key} = {value}")
        logger.success("Параметры LLM обновлены")


# ---------------- Models ----------------

def _parse_models(raw: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            repo, local = item.split(":", 1)
        else:
            repo, local = item, item.split("/")[-1]
        entries.append((repo.strip(), local.strip()))
    return entries


def _enable_online_mode() -> None:
    """Временно включает online-режим для huggingface_hub."""
    for k in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"):
        os.environ[k] = "0"

    # Принудительно правим закешированные константы.
    # Импорт здесь — намеренно поздний, чтобы не поймать старое значение.
    try:
        import huggingface_hub.constants as hf_const
        hf_const.HF_HUB_OFFLINE = False
    except Exception as err:
        logger.debug(f"Не удалось сбросить HF_HUB_OFFLINE константу: {err}")

    try:
        import transformers.utils.hub as tf_hub
        tf_hub._is_offline_mode = False  # type: ignore[attr-defined]
    except Exception:
        pass

    logger.info("HF_HUB_OFFLINE=0 (online-режим для скачивания)")


def cmd_download_models(args: argparse.Namespace) -> None:
    _enable_online_mode()
    try:
        from huggingface_hub import snapshot_download

        models_dir = Path(settings.models_dir).resolve()
        models_dir.mkdir(parents=True, exist_ok=True)

        raw = args.only or settings.models_to_download
        entries = _parse_models(raw)
        if not entries:
            logger.error("Список моделей пуст. Укажите MODELS_TO_DOWNLOAD или --only")
            return

        logger.info(f"Целевая папка: {models_dir}")
        logger.info(f"К скачиванию: {len(entries)} моделей")
        if args.force:
            logger.warning("Режим --force: существующие папки будут перекачаны")

        for repo_id, local_name in entries:
            target = models_dir / local_name
            has_data = target.exists() and any(target.iterdir())

            if has_data and not args.force:
                logger.info(f"[skip] {local_name} уже скачана (--force для перекачки)")
                continue

            if has_data and args.force:
                logger.warning(f"[force] удаляю {target}")
                shutil.rmtree(target, ignore_errors=True)

            logger.info(f"[download] {repo_id} → {target}")
            try:
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=str(target),
                    ignore_patterns=["*.msgpack", "*.h5", "*.ot"],
                )
                logger.success(f"[ok] {local_name}")
            except Exception as err:
                logger.error(f"[fail] {local_name}: {err}")
    finally:
        # Возвращаем offline-режим
        for k in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"):
            os.environ[k] = "1"
        try:
            import huggingface_hub.constants as hf_const
            hf_const.HF_HUB_OFFLINE = True
        except Exception:
            pass
        logger.info("HF_HUB_OFFLINE=1 (offline-режим восстановлен)")


# ---------------- CLI ----------------

def main() -> None:
    parser = argparse.ArgumentParser(description="ConturAI management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Создать таблицы, промты и llm_configs")
    subparsers.add_parser("reset-admin", help="Сбросить пароль админа")

    p_download = subparsers.add_parser("download-models", help="Скачать модели")
    p_download.add_argument("--only", default=None)
    p_download.add_argument("--force", action="store_true")

    p_llm = subparsers.add_parser("set-llm", help="Обновить параметры LLM в БД")
    p_llm.add_argument("--base-url", default=None)
    p_llm.add_argument("--api-key", default=None)
    p_llm.add_argument("--model", default=None)
    p_llm.add_argument("--temperature", default=None)
    p_llm.add_argument("--max-tokens", default=None)

    args = parser.parse_args()

    if args.command == "init-db":
        asyncio.run(cmd_init_db())
    elif args.command == "reset-admin":
        asyncio.run(cmd_reset_admin())
    elif args.command == "download-models":
        cmd_download_models(args)
    elif args.command == "set-llm":
        asyncio.run(cmd_set_llm(args))


if __name__ == "__main__":
    main()