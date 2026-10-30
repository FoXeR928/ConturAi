"""
Изменения относительно предыдущей версии отмечены в activate_plugin():
учтён PLUGIN_ENDPOINT_MODE для выбора endpoint URL контейнера плагина.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

from ..config import settings
from ..interfaces.llm_spec import ContextPipeline, InferenceProvider
from ..interfaces.plugin_spec import NexusPlugin
from .manager_client import ManagerClient

logger = logging.getLogger("conturai.backend.plugins")


class PluginRecord:
    __slots__ = (
        "id", "manifest", "plugin", "status",
        "endpoint_url", "error", "settings", "_installed",
    )

    def __init__(self, plugin_id: str, manifest: dict, plugin: NexusPlugin) -> None:
        self.id = plugin_id
        self.manifest = manifest
        self.plugin = plugin
        self.status = "inactive"
        self.endpoint_url: Optional[str] = None
        self.error: Optional[str] = None
        self.settings: dict = {}
        self._installed = False


class PluginRegistry:
    def __init__(self, plugins_dir: str, manager: ManagerClient) -> None:
        self.plugins_dir = Path(plugins_dir)
        self.manager = manager
        self._plugins: Dict[str, PluginRecord] = {}

    # ---- Discovery --------------------------------------------------------

    def discover(self) -> None:
        if not self.plugins_dir.exists():
            logger.warning("plugins dir does not exist: %s", self.plugins_dir)
            return
        for entry in sorted(self.plugins_dir.iterdir()):
            if not entry.is_dir():
                continue
            try:
                self._discover_one(entry)
            except Exception as exc:
                logger.exception("failed to discover plugin %s: %s", entry.name, exc)

    def _discover_one(self, folder: Path) -> None:
        manifest_path = folder / "manifest.json"
        if not manifest_path.exists():
            return

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        plugin_id = manifest.get("id") or folder.name
        main_path = folder / manifest.get("main", "main.py")
        if not main_path.exists():
            raise RuntimeError(f"main file missing: {main_path}")

        module_name = f"conturai_plugin_{plugin_id}"
        spec = importlib.util.spec_from_file_location(module_name, str(main_path))
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot build spec for {main_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        old_path = list(sys.path)
        sys.path.insert(0, str(folder))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path[:] = old_path

        plugin_cls = self._find_plugin_class(module)
        if plugin_cls is None:
            raise RuntimeError(f"no NexusPlugin subclass in {folder.name}")

        plugin = plugin_cls()
        if not plugin.id:
            plugin.id = plugin_id
        if not plugin.name:
            plugin.name = manifest.get("name", plugin_id)
        plugin.version = manifest.get("version", plugin.version)

        self._plugins[plugin.id] = PluginRecord(plugin.id, manifest, plugin)
        logger.info("discovered plugin: %s [%s]", plugin.id, manifest.get("type", "local"))

    @staticmethod
    def _find_plugin_class(module) -> Optional[type]:
        for attr in dir(module):
            obj = getattr(module, attr)
            if (
                isinstance(obj, type)
                and issubclass(obj, NexusPlugin)
                and obj is not NexusPlugin
            ):
                return obj
        return None

    # ---- Lifecycle --------------------------------------------------------

    async def activate_plugin(self, plugin_id: str) -> None:
        rec = self._plugins.get(plugin_id)
        if rec is None:
            raise KeyError(f"plugin not found: {plugin_id}")
        if rec.status == "active":
            return

        manifest = rec.manifest
        try:
            endpoint_url: Optional[str] = None

            if manifest.get("type") == "remote":
                container_name = manifest.get(
                    "container_name", f"conturai-plugin-{plugin_id}"
                )
                volumes = manifest.get("volumes")
                volumes_map: Optional[Dict[str, str]] = None
                if isinstance(volumes, list):
                    volumes_map = {}
                    for s in volumes:
                        parts = s.split(":")
                        if len(parts) >= 2:
                            volumes_map[parts[0]] = parts[1]
                elif isinstance(volumes, dict):
                    volumes_map = dict(volumes)

                deploy_resp = await self.manager.deploy_plugin(
                    name=container_name,
                    image=manifest["docker_image"],
                    env=manifest.get("environment"),
                    ports=manifest.get("ports"),
                    command=manifest.get("command"),
                    volumes=volumes_map,
                    gpus=bool(manifest.get("gpu", False)),
                )

                internal_port = int(manifest.get("internal_port", 8000))

                if settings.plugin_endpoint_mode == "local":
                    host_port = deploy_resp.get("host_port")
                    if not host_port and manifest.get("ports"):
                        host_port = next(iter(manifest["ports"].values()), None)
                    if not host_port:
                        raise RuntimeError(
                            f"Плагин {plugin_id} не публикует порт на хост — "
                            f"невозможно обратиться из локального backend. "
                            f"Добавьте ports в manifest.json."
                        )
                    endpoint_url = f"http://localhost:{host_port}"
                else:
                    endpoint_url = f"http://{container_name}:{internal_port}"

            if not rec._installed:
                await rec.plugin.on_install()
                rec._installed = True

            await rec.plugin.on_activate(endpoint_url)

            if rec.settings:
                await rec.plugin.apply_settings(rec.settings)

            rec.status = "active"
            rec.endpoint_url = endpoint_url
            rec.error = None
            logger.info("plugin activated: %s (%s)", plugin_id, endpoint_url or "local")

        except Exception as exc:
            logger.exception("activation failed: %s", plugin_id)
            rec.status = "error"
            rec.error = str(exc)
            raise

    async def deactivate_plugin(self, plugin_id: str) -> None:
        rec = self._plugins.get(plugin_id)
        if rec is None:
            raise KeyError(f"plugin not found: {plugin_id}")
        if rec.status != "active":
            return

        try:
            await rec.plugin.on_deactivate()
        except Exception as exc:
            logger.warning("on_deactivate(%s) raised: %s", plugin_id, exc)

        if rec.manifest.get("type") == "remote":
            container_name = rec.manifest.get(
                "container_name", f"conturai-plugin-{plugin_id}"
            )
            try:
                await self.manager.stop_plugin_container(container_name)
            except Exception as exc:
                logger.warning("stop %s failed: %s", container_name, exc)

        rec.status = "inactive"
        rec.endpoint_url = None
        logger.info("plugin deactivated: %s", plugin_id)

    # ---- Chat-доступ ------------------------------------------------------

    def get_inference_provider(self) -> Optional[InferenceProvider]:
        for rec in self._plugins.values():
            if rec.status == "active" and isinstance(rec.plugin, InferenceProvider):
                return rec.plugin
        return None

    def build_context_pipeline(self) -> ContextPipeline:
        pipeline = ContextPipeline()
        for rec in self._plugins.values():
            if rec.status != "active":
                continue
            mw = rec.plugin.get_context_middleware()
            if mw is not None:
                pipeline.add(mw)
        return pipeline

    # ---- Admin ------------------------------------------------------------

    def get(self, plugin_id: str) -> Optional[PluginRecord]:
        return self._plugins.get(plugin_id)

    def list_all(self) -> List[PluginRecord]:
        return list(self._plugins.values())

    async def save_settings(self, plugin_id: str, data: dict) -> dict:
        rec = self._plugins.get(plugin_id)
        if rec is None:
            raise KeyError(f"plugin not found: {plugin_id}")
        blueprint = rec.plugin.get_settings_blueprint()
        if blueprint is None:
            raise ValueError("plugin has no settings schema")
        validated = blueprint(**data)
        rec.settings = validated.model_dump()
        if rec.status == "active":
            await rec.plugin.apply_settings(rec.settings)
        return rec.settings