from __future__ import annotations

import json
from typing import Any

import asyncpg


class PluginStore:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def load_all(self) -> dict[str, dict[str, Any]]:
        rows = await self._pool.fetch(
            "SELECT plugin_id, kind, is_active, settings, external_manifest, endpoint_url "
            "FROM plugins"
        )
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            settings = row["settings"]
            if isinstance(settings, str):
                settings = json.loads(settings)
            external = row["external_manifest"]
            if isinstance(external, str):
                external = json.loads(external)
            result[row["plugin_id"]] = {
                "kind": row["kind"],
                "is_active": row["is_active"],
                "settings": settings or {},
                "external_manifest": external,
                "endpoint_url": row["endpoint_url"],
            }
        return result

    async def upsert(
        self,
        plugin_id: str,
        *,
        kind: str,
        is_active: bool,
        settings: dict[str, Any],
        external_manifest: dict[str, Any] | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        await self._pool.execute(
            """
            INSERT INTO plugins
                (plugin_id, kind, is_active, settings, external_manifest, endpoint_url, updated_at)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, NOW())
            ON CONFLICT (plugin_id) DO UPDATE SET
                kind              = EXCLUDED.kind,
                is_active         = EXCLUDED.is_active,
                settings          = EXCLUDED.settings,
                external_manifest = EXCLUDED.external_manifest,
                endpoint_url      = EXCLUDED.endpoint_url,
                updated_at        = NOW()
            """,
            plugin_id,
            kind,
            is_active,
            json.dumps(settings),
            json.dumps(external_manifest) if external_manifest is not None else None,
            endpoint_url,
        )

    async def delete(self, plugin_id: str) -> None:
        await self._pool.execute(
            "DELETE FROM plugins WHERE plugin_id = $1", plugin_id,
        )