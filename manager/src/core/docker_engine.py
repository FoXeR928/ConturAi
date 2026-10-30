import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import docker
from docker.errors import NotFound, ImageNotFound, APIError
from docker.types import DeviceRequest

from src.config import settings

logger = logging.getLogger("conturai.manager.docker")


def _client():
    return docker.from_env()


class DockerEngine:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._stats_cache: Dict[str, tuple] = {}
        self._stats_cache_ttl = 2.0

    # --- Ресурсы ---------------------------------------------------------

    async def ensure_network(self, name: Optional[str] = None) -> None:
        name = name or settings.network_name

        def _op():
            client = _client()
            try:
                client.networks.get(name)
                logger.info("network '%s' already exists", name)
            except NotFound:
                client.networks.create(name, driver="bridge")
                logger.info("network '%s' created", name)

        await asyncio.to_thread(_op)

    async def ensure_volume(self, name: str) -> None:
        def _op():
            client = _client()
            try:
                client.volumes.get(name)
                logger.info("volume '%s' already exists", name)
            except NotFound:
                client.volumes.create(name=name)
                logger.info("volume '%s' created", name)

        await asyncio.to_thread(_op)

    # --- Образы ----------------------------------------------------------

    async def image_exists(self, image: str) -> bool:
        def _op():
            try:
                _client().images.get(image)
                return True
            except ImageNotFound:
                return False

        return await asyncio.to_thread(_op)

    async def pull_image(self, image: str) -> None:
        def _op():
            client = _client()
            try:
                client.images.get(image)
                return
            except ImageNotFound:
                pass
            logger.info("pulling image '%s' ...", image)
            client.images.pull(image)
            logger.info("image '%s' pulled", image)

        await asyncio.to_thread(_op)

    async def ensure_image(self, image: str, fallback: Optional[str] = None) -> str:
        if await self.image_exists(image):
            return image
        try:
            await self.pull_image(image)
            return image
        except Exception as exc:
            logger.warning("pull failed for %s: %s", image, exc)
            if not fallback:
                raise
        if await self.image_exists(fallback):
            return fallback
        await self.pull_image(fallback)
        return fallback

    # --- Контейнеры ------------------------------------------------------

    async def container_exists(self, name: str) -> bool:
        def _op():
            try:
                _client().containers.get(name)
                return True
            except NotFound:
                return False

        return await asyncio.to_thread(_op)

    async def run_container(
        self,
        *,
        name: str,
        image: str,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, int]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        command: Optional[List[str]] = None,
        network: Optional[str] = None,
        restart_policy: Optional[Dict[str, str]] = None,
        device_requests: Optional[List[DeviceRequest]] = None,
    ) -> None:
        def _op():
            client = _client()
            try:
                existing = client.containers.get(name)
                if existing.status == "running":
                    logger.info("container '%s' already running", name)
                    return
                logger.info("removing stopped container '%s'", name)
                existing.remove(force=True)
            except NotFound:
                pass

            kwargs: Dict[str, Any] = {
                "image": image,
                "name": name,
                "detach": True,
                "environment": environment or {},
                "ports": ports or {},
                "volumes": volumes or {},
                "restart_policy": restart_policy or {"Name": "unless-stopped"},
            }
            if command:
                kwargs["command"] = command
            if network or settings.network_name:
                kwargs["network"] = network or settings.network_name
            if device_requests:
                kwargs["device_requests"] = device_requests

            container = client.containers.run(**kwargs)
            logger.info("container '%s' started (id=%s)", name, container.short_id)

        await asyncio.to_thread(_op)

    async def start_container(self, name: str) -> None:
        def _op():
            _client().containers.get(name).start()

        await asyncio.to_thread(_op)

    async def stop_container(self, name: str, timeout: int = 10) -> None:
        def _op():
            _client().containers.get(name).stop(timeout=timeout)

        await asyncio.to_thread(_op)

    async def restart_container(self, name: str, timeout: int = 10) -> None:
        def _op():
            _client().containers.get(name).restart(timeout=timeout)

        await asyncio.to_thread(_op)

    async def remove_container(self, name: str, force: bool = True) -> None:
        def _op():
            try:
                _client().containers.get(name).remove(force=force)
            except NotFound:
                pass

        await asyncio.to_thread(_op)

    # --- Информация ------------------------------------------------------

    async def get_container_info(self, name: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        cached = self._stats_cache.get(name)
        if cached and (now - cached[0]) < self._stats_cache_ttl:
            return cached[1]
        info = await asyncio.to_thread(self._fetch_container_info, name)
        self._stats_cache[name] = (now, info)
        return info

    def _fetch_container_info(self, name: str) -> Optional[Dict[str, Any]]:
        client = _client()
        try:
            c = client.containers.get(name)
        except NotFound:
            return None

        c.reload()
        state = c.attrs.get("State", {}) or {}
        status = c.status

        info: Dict[str, Any] = {
            "name": name,
            "status": status,
            "image": c.image.tags[0] if c.image.tags else c.image.short_id,
            "uptime_seconds": None,
            "cpu_percent": 0.0,
            "mem_percent": 0.0,
            "mem_usage_mb": 0.0,
            "mem_limit_mb": 0.0,
            "mode": "container",
        }

        started = state.get("StartedAt", "")
        if status == "running" and started:
            try:
                started_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                info["uptime_seconds"] = int(
                    (datetime.now(timezone.utc) - started_dt).total_seconds()
                )
            except Exception:
                pass

        if status == "running":
            try:
                stats = c.stats(stream=False)
                cpu = stats.get("cpu_stats") or {}
                precpu = stats.get("precpu_stats") or {}
                cpu_delta = (cpu.get("cpu_usage") or {}).get("total_usage", 0) - \
                            (precpu.get("cpu_usage") or {}).get("total_usage", 0)
                sys_delta = cpu.get("system_cpu_usage", 0) - precpu.get("system_cpu_usage", 0)
                percpu = (cpu.get("cpu_usage") or {}).get("percpu_usage") or [1]
                n_cpus = len(percpu) or 1
                if sys_delta > 0 and cpu_delta > 0:
                    info["cpu_percent"] = round((cpu_delta / sys_delta) * n_cpus * 100, 2)

                mem = stats.get("memory_stats") or {}
                usage = mem.get("usage", 0) or 0
                limit = mem.get("limit", 0) or 0
                if limit > 0:
                    info["mem_percent"] = round(usage / limit * 100, 2)
                info["mem_usage_mb"] = round(usage / 1024 / 1024, 2)
                info["mem_limit_mb"] = round(limit / 1024 / 1024, 2)
            except (APIError, KeyError, TypeError):
                pass

        return info

    async def get_logs(self, name: str, tail: int = 200) -> str:
        def _op():
            try:
                c = _client().containers.get(name)
                return c.logs(tail=tail).decode("utf-8", errors="replace")
            except NotFound:
                return ""

        return await asyncio.to_thread(_op)

    async def is_installed(self) -> bool:
        return await self.container_exists(settings.backend_name)

    async def get_docker_info(self) -> Dict[str, Any]:
        def _op():
            client = _client()
            v = client.version()
            info = client.info()
            return {
                "server_version": v.get("Version"),
                "api_version": v.get("ApiVersion"),
                "containers_total": info.get("Containers", 0),
                "containers_running": info.get("ContainersRunning", 0),
                "images_total": info.get("Images", 0),
                "gpu_available": "nvidia" in (info.get("Runtimes") or {}),
            }

        try:
            return await asyncio.to_thread(_op)
        except Exception as exc:
            logger.warning("docker info failed: %s", exc)
            return {
                "server_version": None,
                "api_version": None,
                "containers_total": 0,
                "containers_running": 0,
                "images_total": 0,
                "gpu_available": False,
            }

    # --- Плагины ---------------------------------------------------------

    async def deploy_plugin(
        self,
        *,
        name: str,
        image: str,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, int]] = None,
        host_volumes: Optional[Dict[str, str]] = None,
        command: Optional[List[str]] = None,
        gpus: bool = False,
    ) -> None:
        volumes: Dict[str, Dict[str, str]] = {}
        for host_path, container_path in (host_volumes or {}).items():
            volumes[host_path] = {"bind": container_path, "mode": "rw"}

        device_requests = None
        if gpus:
            device_requests = [DeviceRequest(count=-1, capabilities=[["gpu"]])]

        await self.ensure_image(image, fallback=None)
        await self.run_container(
            name=name,
            image=image,
            environment=environment or {},
            ports=ports or {},
            volumes=volumes,
            command=command,
            network=settings.network_name,
            device_requests=device_requests,
        )


engine = DockerEngine()