from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chats, routes
from app.auth.security import hash_password
from app.core.config import settings
from app.db.database import Database
from app.plugins.context import PluginContext
from app.plugins.registry import PluginRegistry
from app.stores.chat_store import ChatStore
from app.stores.plugin_store import PluginStore
from app.stores.user_store import UserStore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("conturai")


BASE_DIR = Path(__file__).resolve().parent.parent
PLUGINS_DIR = BASE_DIR / "plugins"


async def _ensure_admin(user_store: UserStore) -> None:
    if await user_store.count() > 0:
        return
    password = settings.admin_password or secrets.token_urlsafe(12)
    await user_store.create(
        login="admin",
        password_hash=hash_password(password),
        display_name="Администратор",
        role="admin",
    )
    logger.warning("=" * 60)
    logger.warning("Создан администратор. Логин: admin")
    logger.warning("Пароль: %s", password)
    logger.warning("Сохраните пароль — он показывается один раз.")
    logger.warning("=" * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database(settings.database_url)
    await db.connect()

    plugin_store = PluginStore(db.pool)
    user_store = UserStore(db.pool)
    chat_store = ChatStore(db.pool)
    await _ensure_admin(user_store)

    client = httpx.AsyncClient()
    context = PluginContext(database_url=settings.database_url)
    registry = PluginRegistry(PLUGINS_DIR, plugin_store, client, context)
    await registry.load()

    app.state.db = db
    app.state.plugin_store = plugin_store
    app.state.user_store = user_store
    app.state.chat_store = chat_store
    app.state.registry = registry
    app.state.http_client = client

    try:
        yield
    finally:
        await client.aclose()
        await db.close()


app = FastAPI(title="ConturAI Core", version="1.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(routes.router)
