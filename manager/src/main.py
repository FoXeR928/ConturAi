import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.routes.installer_api import router as installer_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("conturai.manager")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="ConturAi manager", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(installer_router)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
else:
    logger.warning("static dir not found: %s", STATIC_DIR)


@app.get("/")
async def index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return {"error": "index.html not found"}
    return FileResponse(str(index_file))


@app.on_event("startup")
async def _on_startup():
    logger.info("ConturAi manager started, static dir=%s", STATIC_DIR)