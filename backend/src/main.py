from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import async_session_factory, init_db
from .routes import auth, chats, sys_admin
from .services.manager_client import ManagerClient
from .services.plugin_loader import PluginRegistry
from .services.user_service import ensure_admin

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("conturai.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. БД
    await init_db()
    async with async_session_factory() as db:
        await ensure_admin(db)

    # 2. Реестр плагинов (discovery, без активации)
    registry = PluginRegistry(settings.plugins_dir, ManagerClient(settings.conturai_manager_url))
    registry.discover()
    app.state.registry = registry

    logger.info(
        "conturai-backend ready | plugins=%d | manager=%s",
        len(registry.list_all()),
        settings.conturai_manager_url,
    )
    yield
    logger.info("conturai-backend shutting down")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(sys_admin.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/admin/plugins", include_in_schema=False)
async def _plugins_noop():
    # placeholder — реальный роут подхватывается из sys_admin.router
    return []