from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from app.plugins.base import BasePlugin
from app.plugins.context import PluginSystemContext
from app.plugins.external import ExternalPlugin
from app.plugins.internal import InternalPlugin
from app.schemas.plugin import (
    ChatMessage,
    PipelineContext,
    PipelineTraceItem,
    PluginManifest,
    PluginView,
)
from app.stores.plugin_store import PluginStore


logger = logging.getLogger(__name__)
SUPPORTED_API_VERSIONS = {"1"}


class PluginRegistry:
    def __init__(
        self,
        plugins_dir: Path,
        plugin_store: PluginStore,
        client: httpx.AsyncClient,
        sys_ctx: PluginSystemContext,
    ) -> None:
        self._plugins_dir = plugins_dir
        self._store = plugin_store
        self._client = client
        self._sys_ctx = sys_ctx
        self._plugins: dict[str, BasePlugin] = {}
        self._endpoints: dict[str, str] = {}
        self._chat_locks: dict[str, asyncio.Lock] = {}
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._health_task: asyncio.Task | None = None

    async def load(self) -> None:
        self._plugins.clear()
        self._endpoints.clear()
        persisted = await self._store.load_all()
        await self._load_internal(persisted)
        self._load_external_from_db(persisted)

    async def _load_internal(self, persisted: dict[str, dict[str, Any]]) -> None:
        if not self._plugins_dir.exists():
            logger.warning("Директория плагинов не найдена: %s", self._plugins_dir)
            return

        for folder in sorted(self._plugins_dir.iterdir()):
            if not folder.is_dir():
                continue
            manifest_path = folder / "manifest.json"
            entry_path = folder / "main.py"
            if not manifest_path.exists() or not entry_path.exists():
                continue

            try:
                raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                raw["kind"] = "internal"
                manifest = PluginManifest.model_validate(raw)
            except Exception as exc:
                logger.exception("Ошибка манифеста %s: %s", folder.name, exc)
                continue

            db_state = persisted.get(manifest.id, {})
            settings = self._merge_settings(manifest, db_state.get("settings"))
            is_active = bool(db_state.get("is_active", manifest.is_active))
            manifest = manifest.model_copy(update={"is_active": is_active})

            try:
                plugin = InternalPlugin(manifest, settings, entry_path, self._sys_ctx)
                await plugin._ensure_loaded()  # type: ignore[attr-defined]
            except Exception as exc:
                logger.exception("Ошибка загрузки %s: %s", manifest.id, exc)
                continue

            plugin.health_status = "ok"
            self._plugins[manifest.id] = plugin
            self._semaphores[manifest.id] = asyncio.Semaphore(manifest.max_concurrent)
            if manifest.id not in persisted:
                await self._persist(plugin)
            logger.info(
                "Загружен internal: %s (priority=%d)",
                manifest.id, manifest.priority,
            )

    def _load_external_from_db(
        self, persisted: dict[str, dict[str, Any]],
    ) -> None:
        for plugin_id, state in persisted.items():
            if state.get("kind") != "external":
                continue
            external = state.get("external_manifest")
            endpoint_url = state.get("endpoint_url")
            if not external or not endpoint_url:
                continue
            try:
                manifest = PluginManifest.model_validate(external)
            except Exception as exc:
                logger.exception("Ошибка восстановления %s: %s", plugin_id, exc)
                continue
            settings = self._merge_settings(manifest, state.get("settings"))
            plugin = ExternalPlugin(manifest, settings, endpoint_url, self._client)
            self._plugins[manifest.id] = plugin
            self._endpoints[manifest.id] = endpoint_url
            self._semaphores[manifest.id] = asyncio.Semaphore(manifest.max_concurrent)
            logger.info("Восстановлен external: %s", manifest.id)

    def _merge_settings(
        self, manifest: PluginManifest, stored: dict[str, Any] | None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            key: field.default
            for key, field in manifest.settings_schema.items()
        }
        if stored:
            for key in result:
                if key in stored:
                    result[key] = stored[key]
        return result

    def list_views(self) -> list[PluginView]:
        return [
            PluginView(
                manifest=p.get_manifest(),
                settings=dict(p.settings),
                health_status=p.health_status,  # type: ignore[arg-type]
            )
            for p in self._plugins.values()
        ]

    def get(self, plugin_id: str) -> BasePlugin | None:
        return self._plugins.get(plugin_id)

    def get_endpoint(self, plugin_id: str) -> str | None:
        return self._endpoints.get(plugin_id)

    def active_pipeline(self) -> list[BasePlugin]:
        """Возвращает активные плагины, отсортированные по priority (по возрастанию)."""
        active = [
            p for p in self._plugins.values()
            if p.get_manifest().is_active
        ]
        active.sort(key=lambda p: p.get_manifest().priority)
        return active

    def get_semaphore(self, plugin_id: str) -> asyncio.Semaphore:
        sem = self._semaphores.get(plugin_id)
        if sem is None:
            sem = asyncio.Semaphore(1)
            self._semaphores[plugin_id] = sem
        return sem

    def get_chat_lock(self, chat_id: str) -> asyncio.Lock:
        lock = self._chat_locks.get(chat_id)
        if lock is None:
            lock = asyncio.Lock()
            self._chat_locks[chat_id] = lock
        return lock

    async def toggle(self, plugin_id: str, is_active: bool) -> PluginView:
        plugin = self._require(plugin_id)
        manifest = plugin.get_manifest().model_copy(update={"is_active": is_active})
        plugin.manifest = manifest
        await self._persist(plugin)
        return PluginView(
            manifest=manifest,
            settings=dict(plugin.settings),
            health_status=plugin.health_status,  # type: ignore[arg-type]
        )

    async def update_settings(
        self, plugin_id: str, raw_settings: dict[str, Any],
    ) -> PluginView:
        plugin = self._require(plugin_id)
        manifest = plugin.get_manifest()
        validated = self._validate_settings(manifest, raw_settings)
        plugin.update_settings(validated)
        await self._persist(plugin)
        try:
            await plugin.reconfigure()
        except Exception as exc:
            logger.exception(
                "reconfigure failed for %s: %s", plugin_id, exc,
            )
        return PluginView(
            manifest=manifest,
            settings=dict(validated),
            health_status=plugin.health_status,  # type: ignore[arg-type]
        )

    async def run_action(self, plugin_id: str, action_id: str) -> None:
        plugin = self._require(plugin_id)
        manifest = plugin.get_manifest()
        if not any(a.id == action_id for a in manifest.actions):
            raise ValueError(f"Действие '{action_id}' не объявлено в манифесте")
        handler = getattr(plugin, f"action_{action_id}", None)
        if handler is None:
            method = f"handle_action_{action_id}"
            inner = getattr(plugin, method, None)
            if inner is not None:
                await inner()
                return
            raise ValueError(f"Плагин '{plugin_id}' не реализует действие '{action_id}'")
        result = handler()
        if asyncio.iscoroutine(result):
            await result

    async def register_external(
        self, manifest: PluginManifest, endpoint_url: str,
    ) -> PluginView:
        if manifest.kind != "external":
            raise ValueError("manifest.kind должен быть 'external'")
        if manifest.api_version not in SUPPORTED_API_VERSIONS:
            raise ValueError(
                f"Несовместимая api_version={manifest.api_version}"
            )
        if not endpoint_url.startswith(("http://", "https://")):
            raise ValueError("endpoint_url должен начинаться с http(s)://")
        url = endpoint_url.rstrip("/")
        try:
            response = await self._client.post(f"{url}/health", timeout=5.0)
            if response.status_code != 200:
                raise ValueError(f"Health-check провалился: HTTP {response.status_code}")
        except httpx.HTTPError as exc:
            raise ValueError(f"Сервер недоступен: {exc}") from exc

        settings = self._merge_settings(manifest, None)
        plugin = ExternalPlugin(manifest, settings, url, self._client)
        plugin.health_status = "ok"
        self._plugins[manifest.id] = plugin
        self._endpoints[manifest.id] = url
        self._semaphores[manifest.id] = asyncio.Semaphore(manifest.max_concurrent)
        await self._persist(plugin)
        return PluginView(
            manifest=manifest, settings=dict(settings), health_status="ok",
        )

    async def delete(self, plugin_id: str) -> None:
        plugin = self._require(plugin_id)
        if plugin.get_manifest().kind != "external":
            raise ValueError("Удалять можно только external-плагины")
        await plugin.shutdown()
        self._plugins.pop(plugin_id, None)
        self._endpoints.pop(plugin_id, None)
        self._semaphores.pop(plugin_id, None)
        await self._store.delete(plugin_id)

    async def check_health(self, plugin_id: str) -> tuple[bool, int]:
        plugin = self._require(plugin_id)
        start = time.monotonic()
        ok = await plugin.check_health()
        latency = int((time.monotonic() - start) * 1000)
        plugin.health_status = "ok" if ok else "down"
        return ok, latency

    async def start_health_loop(self, interval: int) -> None:
        async def _loop() -> None:
            while True:
                try:
                    await asyncio.sleep(interval)
                    for plugin in list(self._plugins.values()):
                        if plugin.get_manifest().kind != "external":
                            continue
                        try:
                            ok = await asyncio.wait_for(
                                plugin.check_health(), timeout=5.0,
                            )
                            plugin.health_status = "ok" if ok else "down"
                        except Exception:
                            plugin.health_status = "down"
                except asyncio.CancelledError:
                    return
                except Exception:
                    logger.exception("health loop error")

        self._health_task = asyncio.create_task(_loop())

    async def shutdown(self) -> None:
        if self._health_task is not None:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
            self._health_task = None
        for plugin in list(self._plugins.values()):
            try:
                await asyncio.wait_for(plugin.shutdown(), timeout=5.0)
            except Exception:
                pass

    def _require(self, plugin_id: str) -> BasePlugin:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise KeyError(f"Плагин '{plugin_id}' не зарегистрирован")
        return plugin

    def _validate_settings(
        self, manifest: PluginManifest, raw: dict[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, field in manifest.settings_schema.items():
            value = raw.get(key, field.default)
            if value is None:
                if field.required:
                    raise ValueError(f"Поле '{key}' обязательно")
                result[key] = None
                continue
            if field.type == "select":
                if not field.options:
                    raise ValueError(f"Поле '{key}': нет options")
                allowed = {opt.get("value") for opt in field.options}
                if value not in allowed:
                    raise ValueError(f"Поле '{key}': недопустимое значение")
            elif field.type in ("slider", "number"):
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    raise ValueError(f"Поле '{key}': требуется число") from None
                if field.min is not None and numeric < field.min:
                    raise ValueError(f"Поле '{key}': меньше минимума")
                if field.max is not None and numeric > field.max:
                    raise ValueError(f"Поле '{key}': больше максимума")
                value = int(numeric) if numeric.is_integer() else numeric
            elif field.type == "boolean":
                value = bool(value)
            elif field.type == "text":
                value = str(value)
            result[key] = value
        return result

    async def _persist(self, plugin: BasePlugin) -> None:
        manifest = plugin.get_manifest()
        await self._store.upsert(
            manifest.id,
            kind=manifest.kind,
            is_active=manifest.is_active,
            settings=plugin.settings,
            external_manifest=(
                manifest.model_dump() if manifest.kind == "external" else None
            ),
            endpoint_url=self._endpoints.get(manifest.id),
        )