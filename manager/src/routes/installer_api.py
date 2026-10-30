import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from src.core.docker_engine import (
    engine,
    NETWORK_NAME,
    POSTGRES_NAME, BACKEND_NAME, FRONTEND_NAME,
    PG_VOLUME, MODELS_VOLUME,
    POSTGRES_IMAGE, BACKEND_IMAGE, FRONTEND_IMAGE, FALLBACK_IMAGE,
    POSTGRES_HOST_PORT, BACKEND_HOST_PORT, FRONTEND_HOST_PORT,
    POSTGRES_ENV, BACKEND_ENV, FRONTEND_ENV,
)

logger = logging.getLogger("conturai.manager.api")
router = APIRouter(prefix="/api")

# ---- Состояние установки ----------------------------------------------------

_INSTALL: Dict[str, Any] = {
    "installing": False,
    "step": "idle",
    "message": "",
    "progress": 0,
    "error": None,
}
_install_lock = asyncio.Lock()


def _set_state(**kwargs) -> None:
    _INSTALL.update(kwargs)


def _reset_state() -> None:
    _INSTALL.update({
        "installing": False, "step": "idle",
        "message": "", "progress": 0, "error": None,
    })


# ---- Модели запросов --------------------------------------------------------

class PluginDeployRequest(BaseModel):
    name: str = Field(..., min_length=1)
    image: str = Field(..., min_length=1)
    env: Optional[Dict[str, str]] = None
    ports: Optional[Dict[str, int]] = None
    command: Optional[List[str]] = None
    volumes: Optional[Dict[str, str]] = None
    gpus: bool = False


# ---- Bootstrap --------------------------------------------------------------

async def _bootstrap_flow() -> None:
    try:
        _set_state(step="network", message="Создание сети " + NETWORK_NAME, progress=5)
        await engine.ensure_network(NETWORK_NAME)

        _set_state(step="volumes", message="Создание томов данных", progress=10)
        await engine.ensure_volume(PG_VOLUME)
        await engine.ensure_volume(MODELS_VOLUME)

        _set_state(step="pull_postgres", message="Загрузка PostgreSQL", progress=20)
        await engine.ensure_image(POSTGRES_IMAGE, fallback=FALLBACK_IMAGE)

        _set_state(step="run_postgres", message="Запуск PostgreSQL", progress=30)
        await engine.run_container(
            name=POSTGRES_NAME,
            image=POSTGRES_IMAGE,
            environment=POSTGRES_ENV,
            ports={"5432/tcp": POSTGRES_HOST_PORT},
            volumes={PG_VOLUME: {"bind": "/var/lib/postgresql/data", "mode": "rw"}},
            network=NETWORK_NAME,
        )
        await asyncio.sleep(4)

        _set_state(step="pull_backend", message="Загрузка бэкенд-ядра", progress=45)
        backend_image = await engine.ensure_image(BACKEND_IMAGE, fallback=FALLBACK_IMAGE)

        _set_state(step="run_backend", message="Запуск бэкенд-ядра", progress=60)
        await engine.run_container(
            name=BACKEND_NAME,
            image=backend_image,
            environment=BACKEND_ENV,
            ports={"8000/tcp": BACKEND_HOST_PORT},
            network=NETWORK_NAME,
            command=["sleep", "infinity"] if backend_image == FALLBACK_IMAGE else None,
        )

        _set_state(step="pull_frontend", message="Загрузка фронтенд-ядра", progress=75)
        frontend_image = await engine.ensure_image(FRONTEND_IMAGE, fallback=FALLBACK_IMAGE)

        _set_state(step="run_frontend", message="Запуск фронтенд-ядра", progress=90)
        await engine.run_container(
            name=FRONTEND_NAME,
            image=frontend_image,
            environment=FRONTEND_ENV,
            ports={"80/tcp": FRONTEND_HOST_PORT},
            network=NETWORK_NAME,
            command=["sleep", "infinity"] if frontend_image == FALLBACK_IMAGE else None,
        )

        _set_state(step="done", message="Установка завершена", progress=100, installing=False)

    except Exception as exc:
        logger.exception("bootstrap failed")
        _set_state(
            step="error",
            message=f"Ошибка установки: {exc}",
            error=str(exc),
            installing=False,
        )


@router.post("/installer/bootstrap")
async def bootstrap() -> Dict[str, Any]:
    if _install_lock.locked() or _INSTALL["installing"]:
        raise HTTPException(status_code=409, detail="Установка уже выполняется")
    if await engine.is_installed():
        raise HTTPException(status_code=409, detail="Система уже установлена")

    async with _install_lock:
        _reset_state()
        _set_state(installing=True, step="start", message="Инициализация установки", progress=1)
        asyncio.create_task(_bootstrap_flow())

    return {"ok": True, "message": "Установка запущена"}


# ---- Статус -----------------------------------------------------------------

@router.get("/installer/status")
async def status() -> Dict[str, Any]:
    installed = await engine.is_installed()

    names = [POSTGRES_NAME, BACKEND_NAME, FRONTEND_NAME]
    try:
        infos = await asyncio.gather(
            *[engine.get_container_info(n) for n in names],
            return_exceptions=True,
        )
    except Exception:
        infos = [None, None, None]

    containers = []
    for n, info in zip(names, infos):
        if isinstance(info, Exception) or info is None:
            containers.append({
                "name": n, "status": "missing", "image": None,
                "uptime_seconds": None, "cpu_percent": 0.0,
                "mem_percent": 0.0, "mem_usage_mb": 0.0, "mem_limit_mb": 0.0,
            })
        else:
            containers.append(info)

    docker_info = await engine.get_docker_info()

    return {
        **_INSTALL,
        "installed": installed,
        "network": NETWORK_NAME,
        "containers": containers,
        "docker": docker_info,
        "ports": {
            "backend":  BACKEND_HOST_PORT,
            "frontend": FRONTEND_HOST_PORT,
            "postgres": POSTGRES_HOST_PORT,
        },
    }


# ---- Управление контейнерами ------------------------------------------------

@router.post("/containers/{name}/start")
async def container_start(name: str):
    if not await engine.container_exists(name):
        raise HTTPException(status_code=404, detail=f"Контейнер {name} не найден")
    try:
        await engine.start_container(name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True, "action": "start", "name": name}


@router.post("/containers/{name}/stop")
async def container_stop(name: str):
    if not await engine.container_exists(name):
        raise HTTPException(status_code=404, detail=f"Контейнер {name} не найден")
    try:
        await engine.stop_container(name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True, "action": "stop", "name": name}


@router.post("/containers/{name}/restart")
async def container_restart(name: str):
    if not await engine.container_exists(name):
        raise HTTPException(status_code=404, detail=f"Контейнер {name} не найден")
    try:
        await engine.restart_container(name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True, "action": "restart", "name": name}


@router.get("/containers/{name}/logs")
async def container_logs(name: str, tail: int = 200):
    if not await engine.container_exists(name):
        raise HTTPException(status_code=404, detail=f"Контейнер {name} не найден")
    logs = await engine.get_logs(name, tail=tail)
    return {"name": name, "tail": tail, "logs": logs}


# ---- Плагины ----------------------------------------------------------------

@router.post("/containers/plugin/deploy")
async def plugin_deploy(payload: PluginDeployRequest = Body(...)):
    if await engine.container_exists(payload.name):
        raise HTTPException(status_code=409, detail=f"Контейнер {payload.name} уже существует")
    try:
        await engine.deploy_plugin(
            name=payload.name,
            image=payload.image,
            environment=payload.env,
            ports=payload.ports,
            host_volumes=payload.volumes,
            command=payload.command,
            gpus=payload.gpus,
        )
    except Exception as exc:
        logger.exception("plugin deploy failed")
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True, "deployed": payload.name}


# ---- Health -----------------------------------------------------------------

@router.get("/health")
async def health():
    return {"status": "ok"}