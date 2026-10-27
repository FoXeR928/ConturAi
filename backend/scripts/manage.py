import argparse
import asyncio
import os
import secrets
import shutil
from pathlib import Path
import subprocess
from datetime import datetime

from loguru import logger
from sqlalchemy import select, text, update, func

from app.core.config import (
    ADMIN_LOGIN,
    ADMIN_NAME,
    SYSTEM_CHAT_ROLE,
    SYSTEM_LOGIN,
    settings,
)
from app.core.logging import setup_logging
from app.core.secrets import load_or_create_jwt_key
from app.db.models import Base, Prompt, User, Document, LlmConfig
from app.db.session import async_session_factory, engine
from app.services import llm_config_service
from app.services.prompt_service import DEFAULT_PROMPTS
from app.rag import embed_texts

# ==============================================================================
# БЛОК 1: ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ (INIT-DB)
# ==============================================================================

async def _create_schema() -> None:
    """Создает все таблицы и расширение vector, если их еще нет."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # create_all автоматически найдет все классы, унаследованные от Base,
        # и создаст для них таблицы (если они не существуют).
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Схема базы данных создана")


async def _seed_prompts(session) -> None:
    """Заполняет таблицу prompts дефолтными значениями из prompt_service."""
    for key, meta in DEFAULT_PROMPTS.items():
        exists = (await session.execute(select(Prompt).where(Prompt.key == key))).scalar_one_or_none()
        if exists is None:
            session.add(Prompt(key=key, value=meta["value"], description=meta["description"]))
    await session.commit()
    logger.info("Промты по умолчанию добавлены")


async def cmd_init_db() -> None:
    """Полная инициализация: создание таблиц, промптов и настроек LLM."""
    setup_logging()
    load_or_create_jwt_key()
    logger.info("Инициализация БД...")
    
    await _create_schema()
    
    async with async_session_factory() as session:
        await _seed_prompts(session)
        await llm_config_service.seed_defaults(session)
        
    logger.success("Инициализация БД завершена")


# ==============================================================================
# БЛОК 2: МИГРАЦИИ (ДОБАВЛЕНИЕ НОВЫХ КОЛОНОК)
# ==============================================================================

async def cmd_migrate() -> None:
    setup_logging()
    logger.info("Применение миграций...")

    # 1. Создание новых таблиц (если появились)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Схема проверена (новые таблицы созданы).")

    # 2. Миграция llm_configs (колонка is_secret)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE llm_configs ADD COLUMN is_secret BOOLEAN DEFAULT FALSE NOT NULL;"))
            logger.info("Колонка 'is_secret' добавлена в llm_configs.")
    except Exception as e:
        logger.debug(f"Колонка 'is_secret' уже существует.")

    # 3. Обновление данных llm_configs (ОТДЕЛЬНАЯ ТРАНЗАКЦИЯ)
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE llm_configs SET is_secret = TRUE WHERE key = 'vllm_api_key';"))
        logger.info("Данные llm_configs обновлены.")

    # 4. Миграция download_requests (для скачивания чатов)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE download_requests ALTER COLUMN upload_id DROP NOT NULL;"))
            await conn.execute(text("ALTER TABLE download_requests ADD COLUMN chat_id UUID REFERENCES chats(id) ON DELETE CASCADE;"))
            logger.info("Колонка 'chat_id' добавлена в download_requests.")
    except Exception as e:
        logger.debug(f"Колонки download_requests уже существуют.")

    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_download_requests_chat_id ON download_requests (chat_id);"))
            logger.info("Индекс 'ix_download_requests_chat_id' создан.")
    except Exception as e:
        logger.debug(f"Ошибка индекса: {e}")

    # 5. Миграция документов (полнотекстовый поиск tsv)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE documents ADD COLUMN tsv tsvector GENERATED ALWAYS AS (to_tsvector('russian', text)) STORED;"))
            logger.info("Колонка 'tsv' добавлена в documents.")
    except Exception as e:
        logger.debug(f"Колонка 'tsv' уже существует.")

    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS documents_tsv_gin ON documents USING GIN (tsv);"))
            logger.info("GIN-индекс для 'tsv' создан.")
    except Exception as e:
        logger.debug(f"Ошибка индекса tsv: {e}")

    # 6. Миграция статистики LLM (messages)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE messages ADD COLUMN prompt_tokens INTEGER DEFAULT 0 NOT NULL;"))
            await conn.execute(text("ALTER TABLE messages ADD COLUMN completion_tokens INTEGER DEFAULT 0 NOT NULL;"))
            await conn.execute(text("ALTER TABLE messages ADD COLUMN duration_ms INTEGER DEFAULT 0 NOT NULL;"))
            logger.info("Колонки статистики LLM добавлены в messages.")
    except Exception as e:
        logger.debug(f"Колонки статистики уже существуют.")

    # 7. Шифрование существующего API-ключа (если нужно)
    from app.core.security import encrypt_secret
    async with async_session_factory() as session:
        cfg = (await session.execute(select(LlmConfig).where(LlmConfig.key == 'vllm_api_key'))).scalar_one_or_none()
        if cfg and cfg.value and not cfg.value.startswith("gAAAA"):
            cfg.value = encrypt_secret(cfg.value)
            await session.commit()
            logger.info("Существующий API-ключ зашифрован.")

    logger.success("Миграция завершена.")


# ==============================================================================
# БЛОК 3: УПРАВЛЕНИЕ АДМИНИСТРАТОРОМ (RESET-ADMIN)
# ==============================================================================

async def cmd_reset_admin() -> None:
    """
    Создает администратора или сбрасывает ему пароль на случайный.
    Также создает системного пользователя, от имени которого отвечает LLM.
    """
    setup_logging()
    async with async_session_factory() as session:
        password = secrets.token_urlsafe(16)
        admin = (await session.execute(select(User).where(User.login == ADMIN_LOGIN))).scalar_one_or_none()
        
        if admin:
            admin.set_password(password)
            admin.role = "admin"  # ИСПРАВЛЕНО: используем role вместо is_admin
            admin.disabled = False
            logger.warning(f"Пароль администратора '{ADMIN_LOGIN}' сброшен.")
        else:
            admin = User(login=ADMIN_LOGIN, user_name=ADMIN_NAME, role="admin") # ИСПРАВЛЕНО
            admin.set_password(password)
            session.add(admin)
            logger.warning(f"Администратор '{ADMIN_LOGIN}' создан.")

        # Создаем скрытого системного пользователя для ответов LLM (если его нет)
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
# БЛОК 4: НАСТРОЙКИ LLM (SET-LLM)
# ==============================================================================

async def cmd_set_llm(args: argparse.Namespace) -> None:
    """Позволяет обновить параметры vLLM напрямую из командной строки."""
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


# ==============================================================================
# БЛОК 5: СКАЧИВАНИЕ МОДЕЛЕЙ С HUGGINGFACE (DOWNLOAD-MODELS)
# ==============================================================================

def _parse_models(raw: str) -> list[tuple[str, str]]:
    """
    Парсит строку формата "repo_id:local_name,repo_id2:local_name2".
    Если local_name не указан, берет последнюю часть repo_id.
    """
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
    """Временно отключает offline-режим HuggingFace для скачивания моделей."""
    for k in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"):
        os.environ[k] = "0"
    try:
        import huggingface_hub.constants as hf_const
        hf_const.HF_HUB_OFFLINE = False
    except Exception:
        pass
    try:
        import transformers.utils.hub as tf_hub
        tf_hub._is_offline_mode = False
    except Exception:
        pass
    logger.info("HF_HUB_OFFLINE=0 (online-режим)")


def cmd_download_models(args: argparse.Namespace) -> None:
    """Скачивает модели (LLM, эмбеддер, реранкер) с HuggingFace."""
    _enable_online_mode()
    try:
        from huggingface_hub import snapshot_download

        models_dir = Path(settings.models_dir).resolve()
        models_dir.mkdir(parents=True, exist_ok=True)

        raw = args.only or settings.models_to_download
        entries = _parse_models(raw)
        if not entries:
            logger.error("Список моделей пуст.")
            return

        logger.info(f"Целевая папка: {models_dir}")
        if args.force:
            logger.warning("Режим --force: существующие папки будут перекачаны")

        for repo_id, local_name in entries:
            target = models_dir / local_name
            has_data = target.exists() and any(target.iterdir())

            if has_data and not args.force:
                logger.info(f"[skip] {local_name} уже скачана")
                continue

            if has_data and args.force:
                logger.warning(f"[force] удаляю {target}")
                shutil.rmtree(target, ignore_errors=True)

            logger.info(f"[download] {repo_id} → {target}")
            try:
                snapshot_download(repo_id=repo_id, local_dir=str(target), ignore_patterns=["*.msgpack", "*.h5", "*.ot"])
                logger.success(f"[ok] {local_name}")
            except Exception as err:
                logger.error(f"[fail] {local_name}: {err}")
    finally:
        # Возвращаем offline-режим (чтобы контейнер не стучался в интернет без надобности)
        for k in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"):
            os.environ[k] = "1"
        try:
            import huggingface_hub.constants as hf_const
            hf_const.HF_HUB_OFFLINE = True
        except Exception:
            pass
        logger.info("HF_HUB_OFFLINE=1 (offline-режим)")


# ==============================================================================
# БЛОК 6: ПЕРЕИНДЕКСАЦИЯ ДОКУМЕНТОВ (REEMBED)
# ==============================================================================

async def cmd_reembed() -> None:
    """
    Пересчитывает вектора (эмбеддинги) для всех чанков в базе.
    Нужно, если вы сменили модель эмбеддингов (EMBEDDING_MODEL_PATH).
    """
    setup_logging()
    logger.info("Запуск переиндексации документов...")
    async with async_session_factory() as session:
        total = (await session.execute(select(func.count(Document.id)))).scalar_one()
        if total == 0:
            logger.info("База документов пуста.")
            return

        logger.info(f"Найдено {total} чанков. Начинаем пересчет...")
        BATCH_SIZE = 64
        processed = 0
        
        result = await session.execute(select(Document.id, Document.text).order_by(Document.created_at))
        rows = result.all()
        
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            texts = [row.text for row in batch]
            vectors = await embed_texts(texts)
            
            for row, vector in zip(batch, vectors):
                await session.execute(
                    update(Document).where(Document.id == row.id).values(embedding=vector)
                )
            
            await session.commit()
            processed += len(batch)
            logger.info(f"Обработано {processed}/{total} чанков...")

    logger.success("Переиндексация успешно завершена!")


# ==============================================================================
# БЛОК 7: РЕЗЕРВНОЕ КОПИРОВАНИЕ (BACKUP)
# ==============================================================================

async def cmd_backup() -> None:
    """Создает дамп базы данных (pg_dump) и ZIP-архив загруженных файлов."""
    setup_logging()
    backup_dir = Path("./data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Дамп БД
    db_file = backup_dir / f"db_{timestamp}.sql"
    logger.info(f"Создание дампа БД: {db_file}")
    
    env = os.environ.copy()
    env["PGPASSWORD"] = settings.db_password
    
    try:
        subprocess.run(
            ["pg_dump", "-h", settings.db_host, "-U", settings.db_user, "-d", settings.db_name, "-f", str(db_file)],
            env=env, check=True, capture_output=True
        )
        logger.info("Дамп БД успешно создан.")
    except FileNotFoundError:
        logger.error("pg_dump не найден. Установите postgresql-client в контейнер.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка pg_dump: {e.stderr.decode()}")
    
    # 2. Архив загрузок
    zip_file = backup_dir / f"uploads_{timestamp}"
    logger.info(f"Архивация загрузок: {zip_file}.zip")
    shutil.make_archive(str(zip_file), 'zip', "./data/uploads")
    logger.success("Бэкап завершен!")


# ==============================================================================
# БЛОК 8: CLI ИНТЕРФЕЙС (ARGPARSE)
# ==============================================================================

def main() -> None:
    """Главная точка входа для CLI. Регистрирует команды и вызывает нужную функцию."""
    parser = argparse.ArgumentParser(description="ConturAI management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Создать таблицы, промты и llm_configs")
    subparsers.add_parser("reset-admin", help="Сбросить пароль админа")
    subparsers.add_parser("migrate", help="Применить новые колонки в БД")
    subparsers.add_parser("reembed", help="Переиндексировать все документы")
    subparsers.add_parser("backup", help="Резервное копирование")

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
    elif args.command == "migrate":
        asyncio.run(cmd_migrate())
    elif args.command == "reembed":
        asyncio.run(cmd_reembed())
    elif args.command == "backup":
        asyncio.run(cmd_backup())


if __name__ == "__main__":
    main()