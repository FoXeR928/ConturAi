import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.routes.installer_api import router as installer_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("conturai.manager")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="ConturAi manager", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(installer_router)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    f = STATIC_DIR / "index.html"
    return FileResponse(str(f)) if f.exists() else {"error": "index.html missing"}


@app.on_event("startup")
async def _startup():
    logger.info(
        "ConturAi manager started | local_mode=%s | port=%s",
        settings.local_mode, settings.manager_port,
    )