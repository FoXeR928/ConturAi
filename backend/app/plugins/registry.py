from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import httpx

from app.plugins.base import BasePlugin
from app.plugins.context import PluginContext
from app.plugins.external import ExternalPlugin
from app.plugins.internal import InternalPlugin
from app.schemas.plugin import PluginManifest, PluginView
from app.stores.plugin_store import PluginStore


logger = logging.getLogger(__name__)


class PluginRegistry:
    def __init__(
        self,
        plugins_dir: Path,
        plugin_store: PluginStore,
        client: httpx.AsyncClient,
        context: PluginContext,
    ) -> None:
        self._plugins_dir = plugins_dir
        self._store = plugin_store
        self._client = client
        self._context = context
        self._plugins: dict[str, BasePlugin] = {}
        self._endpoints: dict[str, str] = {}

    async def load(self) -> None:
        self._plugins.clear()
        self._endpoints.clear()
        persisted = await self._store.load_all()
        await self._load_internal(persisted)
        self._load_external_from_db(persisted)

    async def _load_internal(
        self, persisted: dict[str, dict[str, Any]],
    ) -> None:
        if not self._plugins_dir.exists():
            logger.warning(
                "Директория плагинов не найдена: %s", self._plugins_dir,
            )
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
                logger.exception(
                    "Ошибка манифеста %s: %s", folder.name, exc,
                )
                continue

            db_state = persisted.get(manifest.id, {})
            settings = self._merge_settings(
                manifest, db_state.get("settings"),
            )
            is_active = bool(
                db_state.get("is_active", manifest.is_active),
            )
            manifest = manifest.model_copy(update={"is_active": is_active})

            try:
                plugin = InternalPlugin(
                    manifest, settings, entry_path, self._context,
                )
                await plugin.setup()
            except Exception as exc:
                logger.exception(
                    "Ошибка инициализации %s: %s", manifest.id, exc,
                )
                continue

            self._plugins[manifest.id] = plugin
            if manifest.id not in persisted:
                await self._persist(plugin)
            logger.info("Загружен internal-плагин: %s", manifest.id)

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
                logger.exception(
                    "Ошибка восстановления %s: %s", plugin_id, exc,
                )
                continue
            settings = self._merge_settings(
                manifest, state.get("settings"),
            )
            plugin = ExternalPlugin(
                manifest, settings, endpoint_url, self._client,
            )
            self._plugins[manifest.id] = plugin
            self._endpoints[manifest.id] = endpoint_url
            logger.info(
                "Восстановлен external-плагин: %s → %s",
                manifest.id, endpoint_url,
            )

    def _merge_settings(
        self,
        manifest: PluginManifest,
        stored: dict[str, Any] | None,
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
                manifest=p.get_manifest(), settings=dict(p.settings),
            )
            for p in self._plugins.values()
        ]

    def get(self, plugin_id: str) -> BasePlugin | None:
        return self._plugins.get(plugin_id)

    async def toggle(
        self, plugin_id: str, is_active: bool,
    ) -> PluginView:
        plugin = self._require(plugin_id)
        manifest = plugin.get_manifest().model_copy(
            update={"is_active": is_active},
        )
        plugin.manifest = manifest
        await self._persist(plugin)
        return PluginView(
            manifest=manifest, settings=dict(plugin.settings),
        )

    async def update_settings(
        self, plugin_id: str, raw_settings: dict[str, Any],
    ) -> PluginView:
        plugin = self._require(plugin_id)
        manifest = plugin.get_manifest()
        validated = self._validate_settings(manifest, raw_settings)
        plugin.update_settings(validated)
        await self._persist(plugin)
        return PluginView(manifest=manifest, settings=dict(validated))

    async def register_external(
        self, manifest: PluginManifest, endpoint_url: str,
    ) -> PluginView:
        if manifest.kind != "external":
            raise ValueError(
                "register_external ожидает manifest.kind='external'",
            )
        if not endpoint_url.startswith(("http://", "https://")):
            raise ValueError(
                "endpoint_url должен начинаться с http:// или https://",
            )

        settings = self._merge_settings(manifest, None)
        plugin = ExternalPlugin(
            manifest, settings, endpoint_url, self._client,
        )
        self._plugins[manifest.id] = plugin
        self._endpoints[manifest.id] = endpoint_url
        await self._persist(plugin)
        return PluginView(manifest=manifest, settings=dict(settings))

    def _require(self, plugin_id: str) -> BasePlugin:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise KeyError(
                f"Плагин '{plugin_id}' не зарегистрирован",
            )
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
                    raise ValueError(
                        f"Поле '{key}': в схеме отсутствуют options",
                    )
                allowed = {opt.get("value") for opt in field.options}
                if value not in allowed:
                    raise ValueError(
                        f"Поле '{key}': недопустимое значение",
                    )
            elif field.type in ("slider", "number"):
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"Поле '{key}': требуется число",
                    ) from None
                if field.min is not None and numeric < field.min:
                    raise ValueError(
                        f"Поле '{key}': меньше минимума",
                    )
                if field.max is not None and numeric > field.max:
                    raise ValueError(
                        f"Поле '{key}': больше максимума",
                    )
                value = (
                    int(numeric) if numeric.is_integer() else numeric
                )
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
                manifest.model_dump()
                if manifest.kind == "external"
                else None
            ),
            endpoint_url=self._endpoints.get(manifest.id),
        )