import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from src.config import settings
from src.core.docker_engine import engine

logger = logging.getLogger("conturai.manager.api")
router = APIRouter(prefix="/api")

_INSTALL: Dict[str, Any] = {
    "installing": False,
    "step": "idle",
    "message": "",
    "progress": 0,
    "error": None,
}
_install_lock = asyncio.Lock()


def _set_state(**kw) -> None:
    _INSTALL.update(kw)


def _reset_state() -> None:
    _INSTALL.update({
        "installing": False, "step": "idle",
        "message": "", "progress": 0, "error": None,
    })


class PluginDeployRequest(BaseModel):
    name: str = Field(..., min_length=1)
    image: str = Field(..., min_length=1)
    env: Optional[Dict[str, str]] = None
    ports: Optional[Dict[str, int]] = None
    command: Optional[List[str]] = None
    volumes: Optional[Dict[str, str]] = None
    gpus: bool = False


# ---- HTTP check helpers -----------------------------------------------------

async def _http_ok(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as c:
            r = await c.get(url)
            return r.status_code < 500
    except Exception:
        return False


def _process_info(name: str, image_hint: str, alive: bool) -> Dict[str, Any]:
    return {
        "name": name,
        "status": "running" if alive else "missing",
        "image": image_hint,
        "uptime_seconds": None,
        "cpu_percent": 0.0,
        "mem_percent": 0.0,
        "mem_usage_mb": 0.0,
        "mem_limit_mb": 0.0,
        "mode": "process",
    }


def _missing_info(name: str) -> Dict[str, Any]:
    return {
        "name": name,
        "status": "missing",
        "image": None,
        "uptime_seconds": None,
        "cpu_percent": 0.0,
        "mem_percent": 0.0,
        "mem_usage_mb": 0.0,
        "mem_limit_mb": 0.0,
        "mode": "container",
    }


# ---- Bootstrap --------------------------------------------------------------

async def _bootstrap_flow() -> None:
    try:
        _set_state(step="network", message=f"Создание сети {settings.network_name}", progress=10)
        await engine.ensure_network()

        _set_state(step="volumes", message="Создание томов данных", progress=20)
        await engine.ensure_volume(settings.pg_volume)
        await engine.ensure_volume(settings.models_volume)

        _set_state(step="pull_postgres", message="Загрузка PostgreSQL", progress=35)
        await engine.ensure_image(settings.postgres_image, fallback=settings.fallback_image)

        _set_state(step="run_postgres", message="Запуск PostgreSQL", progress=55)
        await engine.run_container(
            name=settings.postgres_name,
            image=settings.postgres_image,
            environment=settings.postgres_env,
            ports={"5432/tcp": settings.postgres_host_port},
            volumes={settings.pg_volume: {"bind": "/var/lib/postgresql/data", "mode": "rw"}},
        )
        await asyncio.sleep(4)

        if settings.local_mode:
            _set_state(
                step="done",
                message="Инфраструктура БД готова. Backend/Frontend запустите локально (scripts/dev.py).",
                progress=100,
                installing=False,
            )
            return

        # Production путь — поднимаем backend и frontend как контейнеры
        _set_state(step="pull_backend", message="Загрузка бэкенд-ядра", progress=70)
        backend_image = await engine.ensure_image(settings.backend_image, fallback=settings.fallback_image)

        _set_state(step="run_backend", message="Запуск бэкенд-ядра", progress=80)
        await engine.run_container(
            name=settings.backend_name,
            image=backend_image,
            environment=settings.backend_env,
            ports={"8000/tcp": settings.backend_host_port},
            command=["sleep", "infinity"] if backend_image == settings.fallback_image else None,
        )

        _set_state(step="pull_frontend", message="Загрузка фронтенд-ядра", progress=90)
        frontend_image = await engine.ensure_image(settings.frontend_image, fallback=settings.fallback_image)

        _set_state(step="run_frontend", message="Запуск фронтенд-ядра", progress=95)
        await engine.run_container(
            name=settings.frontend_name,
            image=frontend_image,
            environment=settings.frontend_env,
            ports={"80/tcp": settings.frontend_host_port},
            command=["sleep", "infinity"] if frontend_image == settings.fallback_image else None,
        )

        _set_state(step="done", message="Установка завершена", progress=100, installing=False)

    except Exception as exc:
        logger.exception("bootstrap failed")
        _set_state(step="error", message=f"Ошибка установки: {exc}", error=str(exc), installing=False)


@router.post("/installer/bootstrap")
async def bootstrap() -> Dict[str, Any]:
    if _install_lock.locked() or _INSTALL["installing"]:
        raise HTTPException(status_code=409, detail="Установка уже выполняется")

    if not settings.local_mode and await engine.is_installed():
        raise HTTPException(status_code=409, detail="Система уже установлена")

    async with _install_lock:
        _reset_state()
        _set_state(installing=True, step="start", message="Инициализация установки", progress=1)
        asyncio.create_task(_bootstrap_flow())

    return {"ok": True, "message": "Установка запущена"}


# ---- Status -----------------------------------------------------------------

@router.get("/installer/status")
async def status() -> Dict[str, Any]:
    containers: List[Dict[str, Any]] = []

    # Postgres — всегда контейнер
    pg_info = await engine.get_container_info(settings.postgres_name)
    containers.append(pg_info or _missing_info(settings.postgres_name))

    # Backend / Frontend
    if settings.local_mode:
        b_ok, f_ok = await asyncio.gather(
            _http_ok(settings.backend_health_url),
            _http_ok(settings.frontend_health_url),
        )
        containers.append(_process_info(settings.backend_name, "(local process)", b_ok))
        containers.append(_process_info(settings.frontend_name, "(local process)", f_ok))
    else:
        b = await engine.get_container_info(settings.backend_name)
        f = await engine.get_container_info(settings.frontend_name)
        containers.append(b or _missing_info(settings.backend_name))
        containers.append(f or _missing_info(settings.frontend_name))

    # Обнаруживаем дополнительные контейнеры плагинов
    def _list_plugin_containers() -> List[Dict[str, Any]]:
        try:
            import docker
            client = docker.from_env()
            out = []
            for c in client.containers.list(all=True):
                names = [t for t in c.name.split(",")] if c.name else []
                if any(n.startswith("conturai-plugin-") for n in names):
                    out.append({
                        "name": c.name,
                        "status": c.status,
                        "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                        "uptime_seconds": None,
                        "cpu_percent": 0.0,
                        "mem_percent": 0.0,
                        "mem_usage_mb": 0.0,
                        "mem_limit_mb": 0.0,
                        "mode": "container",
                        "plugin": True,
                    })
            return out
        except Exception:
            return []

    containers.extend(await asyncio.to_thread(_list_plugin_containers))

    installed = (
        await engine.is_installed()
        or (settings.local_mode and await _http_ok(settings.backend_health_url))
    )
    docker_info = await engine.get_docker_info()

    return {
        **_INSTALL,
        "installed": installed,
        "local_mode": settings.local_mode,
        "network": settings.network_name,
        "containers": containers,
        "docker": docker_info,
        "ports": {
            "backend":  settings.backend_host_port,
            "frontend": settings.frontend_host_port,
            "postgres": settings.postgres_host_port,
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
    if settings.local_mode and name in (settings.backend_name, settings.frontend_name):
        return {
            "name": name,
            "tail": tail,
            "logs": f"[{name}] работает как локальный процесс — см. терминал scripts/dev.py",
        }
    if not await engine.container_exists(name):
        raise HTTPException(status_code=404, detail=f"Контейнер {name} не найден")
    return {"name": name, "tail": tail, "logs": await engine.get_logs(name, tail=tail)}


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

    host_port = None
    if payload.ports:
        host_port = next(iter(payload.ports.values()), None)

    return {
        "ok": True,
        "deployed": payload.name,
        "host_port": host_port,
        "internal_url": f"http://{payload.name}:8000",
        "external_url": f"http://localhost:{host_port}" if host_port else None,
    }


@router.delete("/containers/{name}")
async def container_remove(name: str):
    await engine.remove_container(name, force=True)
    return {"ok": True, "removed": name}


@router.get("/health")
async def health():
    return {"status": "ok", "local_mode": settings.local_mode}