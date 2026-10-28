from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text, select
from datetime import datetime, timezone, timedelta

from app.api.router import api_router
from app.core.config import settings, APP_VERSION
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.db.session import async_session_factory, engine
from app.db.models import Upload, Document
from app.services import file_storage

# ==============================================================================
# БЛОК 1: ИНИЦИАЛИЗАЦИЯ ПЛАНИРОВЩИКА ФОНОВЫХ ЗАДАЧ
# ==============================================================================

# AsyncIOScheduler позволяет запускать задачи по расписанию, 
# не блокируя основной поток FastAPI.
scheduler = AsyncIOScheduler()


# ==============================================================================
# БЛОК 2: ФОНОВЫЕ ЗАДАЧИ (ОЧИСТКА И ОПТИМИЗАЦИЯ)
# ==============================================================================

async def daily_cleanup_orphans():
    """
    Ежедневная очистка "мусорных" загрузок.
    
    Ситуация: пользователь загрузил PDF-файл (он сохранился на диск и в таблицу Upload), 
    но передумал и не нажал "Добавить в RAG" (в таблицу Document ничего не попало).
    Такие файлы занимают место на диске.
    
    Задача находит загрузки старше 24 часов, у которых нет связанных чанков в RAG, 
    и безвозвратно удаляет их (и с диска, и из БД).
    """
    logger.info("Запуск очистки 'мусорных' загрузок...")
    try:
        async with async_session_factory() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            
            # Ищем Upload, у которых нет ни одного Document (через LEFT JOIN)
            stmt = select(Upload).outerjoin(Document).where(
                Document.id.is_(None), 
                Upload.created_at < cutoff
            )
            orphans = (await session.execute(stmt)).scalars().all()
            
            for upload in orphans:
                file_storage.delete_file(upload.stored_name)
                await session.delete(upload)
            
            await session.commit()
            logger.info(f"Удалено {len(orphans)} сиротских загрузок.")
    except Exception as e:
        logger.error(f"Ошибка очистки: {e}")


async def weekly_db_maintenance():
    """
    Еженедельная оптимизация БД.
    
    В PostgreSQL при частом удалении документов (например, при переиндексации) 
    остается "мертвое" место, а HNSW-индекс (для векторного поиска) может замедлиться.
    
    VACUUM ANALYZE собирает статистику и освобождает место.
    REINDEX пересобирает индекс, чтобы поиск по векторам снова работал быстро.
    """
    logger.info("Запуск еженедельной оптимизации БД (VACUUM ANALYZE)...")
    try:
        # VACUUM нельзя запускать внутри транзакции, поэтому используем AUTOCOMMIT
        async with engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(text("VACUUM ANALYZE documents;"))
            await conn.execute(text("REINDEX INDEX documents_embedding_hnsw;"))
        logger.success("Еженедельная оптимизация БД и индекса завершена.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении VACUUM: {e}")


# ==============================================================================
# БЛОК 3: ЖИЗНЕННЫЙ ЦИКЛ ПРИЛОЖЕНИЯ (LIFESPAN)
# ==============================================================================

@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Управляет запуском и остановкой приложения.
    Всё, что находится ДО `yield`, выполняется при старте.
    Всё, что ПОСЛЕ — при выключении (graceful shutdown).
    """
    # --- СТАРТ ---
    setup_logging()
    logger.info("Starting ConturAI...")
    
    # Регистрируем фоновые задачи
    # 1. Оптимизация БД: каждое воскресенье в 3:00 ночи
    scheduler.add_job(
        weekly_db_maintenance,
        CronTrigger(day_of_week='sun', hour=3, minute=0),
        id="db_vacuum_job",
        replace_existing=True
    )
    # 2. Очистка мусора: каждый день в 4:00 утра
    scheduler.add_job(
        daily_cleanup_orphans, 
        CronTrigger(hour=4, minute=0), 
        id="cleanup_job"
    )
    
    scheduler.start()
    logger.info("Планировщик фоновых задач запущен.")
    
    yield # <-- Здесь приложение работает и принимает запросы
    
    # --- ОСТАНОВКА ---
    scheduler.shutdown()
    logger.info("Shutdown")


# ==============================================================================
# БЛОК 4: СОЗДАНИЕ ПРИЛОЖЕНИЯ FASTAPI
# ==============================================================================

app = FastAPI(
    title=settings.app_name, 
    version=APP_VERSION, 
    lifespan=lifespan
)


# ==============================================================================
# БЛОК 5: ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ ОШИБОК (EXCEPTION HANDLERS)
# ==============================================================================

@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """
    Обработчик для кастомных бизнес-ошибок (AppError).
    Формирует стандартный JSON-ответ с полями result, message и category, 
    который ожидает фронтенд.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "result": exc.result,
            "message": exc.message,
            "category": exc.category,
        },
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Глобальный обработчик для ЛЮБЫХ непредвиденных ошибок (500).
    Не дает FastAPI вернуть стандартную HTML-страницу с ошибкой (что сломало бы
    парсинг JSON на фронтенде). Вместо этого логирует ошибку и возвращает JSON.
    """
    logger.exception(f"Необработанная ошибка на {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "result": False,
            "message": "Внутренняя ошибка сервера. Проверьте логи.",
            "category": "error",
        },
    )


# ==============================================================================
# БЛОК 6: ПОДКЛЮЧЕНИЕ РОУТЕРОВ И ЗАПУСК
# ==============================================================================

# Подключаем все эндпоинты (auth, chats, ai и т.д.)
app.include_router(api_router)


def run() -> None:
    """
    Точка входа для запуска через `python -m app.main`.
    Используется в Dockerfile как CMD.
    """
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        log_config=None, # Отключаем стандартное логирование uvicorn (у нас есть Loguru)
    )


if __name__ == "__main__":
    run()