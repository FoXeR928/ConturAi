"""
Тонкий HTTP-клиент к ConturAi manager.
Отвечает исключительно за операции с инфраструктурой (Docker-контейнеры).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("conturai.backend.manager")


class ManagerClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(180.0, connect=10.0)

    # ---- Deploy / Stop ----------------------------------------------------

    async def deploy_plugin(
        self,
        *,
        name: str,
        image: str,
        env: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, int]] = None,
        command: Optional[List[str]] = None,
        volumes: Optional[Dict[str, str]] = None,
        gpus: bool = False,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "name": name,
            "image": image,
            "gpus": gpus,
        }
        if env:
            payload["env"] = env
        if ports:
            payload["ports"] = ports
        if command:
            payload["command"] = command
        if volumes:
            payload["volumes"] = volumes

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(
                f"{self.base_url}/api/containers/plugin/deploy", json=payload
            )
            if r.status_code == 409:
                # Контейнер уже существует — пробуем стартовать его.
                logger.info("container %s exists, starting it", name)
                r2 = await client.post(
                    f"{self.base_url}/api/containers/{name}/start"
                )
                r2.raise_for_status()
                return {"status": "started", "name": name, "reused": True}
            r.raise_for_status()
            return r.json()

    async def stop_plugin_container(self, name: str) -> None:
        """Останавливает и (если API поддерживает) удаляет контейнер."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            # Расширенный (желаемый) API: DELETE /api/containers/{name}
            try:
                r = await client.delete(
                    f"{self.base_url}/api/containers/{name}"
                )
                if r.status_code == 404:
                    return
                if r.status_code < 400:
                    return
            except httpx.HTTPError:
                pass

            # Фолбэк: POST /api/containers/{name}/stop
            r = await client.post(
                f"{self.base_url}/api/containers/{name}/stop"
            )
            if r.status_code == 404:
                return
            r.raise_for_status()

    # ---- Status -----------------------------------------------------------

    async def get_status(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{self.base_url}/api/installer/status")
            r.raise_for_status()
            return r.json()