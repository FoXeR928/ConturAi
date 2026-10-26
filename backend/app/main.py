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

# Глобальный планировщик
scheduler = AsyncIOScheduler()

async def daily_cleanup_orphans():
    """Удаляет файлы, которые загрузили, но не добавили в RAG"""
    logger.info("Запуск очистки 'мусорных' загрузок...")
    try:
        async with async_session_factory() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            
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
    """Фоновая задача для оптимизации БД"""
    logger.info("Запуск еженедельной оптимизации БД (VACUUM ANALYZE)...")
    try:
        # VACUUM нельзя запускать в транзакции, используем отдельное подключение
        async with engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(text("VACUUM ANALYZE documents;"))
            await conn.execute(text("REINDEX INDEX documents_embedding_hnsw;"))
        logger.success("Еженедельная оптимизация БД и индекса завершена.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении VACUUM: {e}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    logger.info("Starting ConturAI...")
    
    scheduler.add_job(
        weekly_db_maintenance,
        CronTrigger(day_of_week='sun', hour=3, minute=0),
        id="db_vacuum_job",
        replace_existing=True
    )
    scheduler.add_job(daily_cleanup_orphans, CronTrigger(hour=4, minute=0), id="cleanup_job")
    scheduler.start()
    logger.info("Планировщик фоновых задач запущен.")
    
    yield
    
    scheduler.shutdown()
    logger.info("Shutdown")

app = FastAPI(title=settings.app_name, version=APP_VERSION, lifespan=lifespan)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
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
    logger.exception(f"Необработанная ошибка на {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "result": False,
            "message": "Внутренняя ошибка сервера. Проверьте логи.",
            "category": "error",
        },
    )

app.include_router(api_router)


def run() -> None:
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        log_config=None,
    )

if __name__ == "__main__":
    run()