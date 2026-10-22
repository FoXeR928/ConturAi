from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.router import api_router
from app.core.config import settings, APP_VERSION
from app.core.exceptions import AppError
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    logger.info("Starting ConturAI...")
    yield
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