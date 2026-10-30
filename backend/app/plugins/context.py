from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PluginSystemContext:
    """Системный контекст — передаётся один раз при configure().
    Содержит разделяемые ресурсы (pool, http, docker). Плагин может их
    использовать, но не владеет ими."""

    database_url: str
    http_client: Any = None
    docker_client: Any = None
    docker_network: str = ""