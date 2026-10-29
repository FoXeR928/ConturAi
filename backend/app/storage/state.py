from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any


class StateStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        self._data: dict[str, dict[str, Any]] = {}

    async def load(self) -> None:
        async with self._lock:
            if not self._path.exists():
                self._data = {}
                return
            try:
                raw = self._path.read_text(encoding="utf-8")
                parsed = json.loads(raw)
                self._data = parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def get(self, plugin_id: str) -> dict[str, Any]:
        return self._data.get(plugin_id, {})

    def all(self) -> dict[str, dict[str, Any]]:
        return self._data

    async def set(self, plugin_id: str, value: dict[str, Any]) -> None:
        async with self._lock:
            self._data[plugin_id] = value
            self._flush()

    async def delete(self, plugin_id: str) -> None:
        async with self._lock:
            self._data.pop(plugin_id, None)
            self._flush()

    def _flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, self._path)