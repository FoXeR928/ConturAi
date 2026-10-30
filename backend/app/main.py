from __future__ import annotations

import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chats, proxy, routes, users
from app.auth.security import hash_password
from app.core.config import settings
from app.core.errors import install_error_handlers
from app.db.database import Database
from app.plugins.context import PluginSystemContext
from app.plugins.registry import PluginRegistry
from app.stores.chat_store import ChatStore
from app.stores.plugin_store import PluginStore
from app.stores.user_store import UserStore

try:
    import docker
    from docker import DockerClient
    _DOCKER_AVAILABLE = True
except ImportError:
    _DOCKER_AVAILABLE = False
    DockerClient = None  # type: ignore


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

    docker_client = None
    if _DOCKER_AVAILABLE:
        try:
            docker_client = docker.from_env()
            docker_client.ping()
            logger.info("Docker SDK подключён")
        except Exception as exc:
            logger.warning("Docker SDK недоступен: %s", exc)
            docker_client = None
    else:
        logger.warning("Модуль docker не установлен — managed-плагины недоступны")

    sys_ctx = PluginSystemContext(
        database_url=settings.database_url,
        http_client=client,
        docker_client=docker_client,
        docker_network=os.getenv("DOCKER_NETWORK", "conturai_conturai"),
    )

    registry = PluginRegistry(PLUGINS_DIR, plugin_store, client, sys_ctx)
    await registry.load()
    await registry.start_health_loop(settings.external_plugin_health_interval)

    app.state.db = db
    app.state.plugin_store = plugin_store
    app.state.user_store = user_store
    app.state.chat_store = chat_store
    app.state.registry = registry
    app.state.http_client = client
    app.state.docker_client = docker_client

    try:
        yield
    finally:
        await registry.shutdown()
        await client.aclose()
        await db.close()


app = FastAPI(title="ConturAI Core", version="3.0.0", lifespan=lifespan)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

install_error_handlers(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(chats.router)
app.include_router(routes.router)
app.include_router(proxy.router)