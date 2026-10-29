from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PluginContext:
    """Системный контекст, передаваемый плагинам при configure()."""
    database_url: str