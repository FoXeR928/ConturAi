from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field


FieldType = Literal["select", "slider", "number", "text", "boolean"]
HealthStatus = Literal["ok", "down", "unknown"]
PluginKind = Literal["internal", "external"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


@dataclass
class PipelineContext:
    """Состояние, которое передаётся по цепочке плагинов.
    Плагины могут модифицировать поля (в т.ч. in place) и возвращать тот же объект."""

    prompt: str
    history: list[ChatMessage] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    answer: str | None = None


class SettingsFieldSchema(BaseModel):
    type: FieldType
    label: str
    default: Any = None
    description: str | None = None
    required: bool = True
    options: list[dict[str, Any]] | None = None
    min: float | None = None
    max: float | None = None
    step: float | None = None


class PluginAction(BaseModel):
    id: str = Field(..., pattern=r"^[a-z0-9_\-]+$")
    label: str
    confirm: bool = False
    description: str | None = None


class PluginManifest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_\-]+$")
    name: str
    description: str = ""
    version: str = "1.0.0"
    api_version: str = "1"
    kind: PluginKind
    is_active: bool = True
    priority: int = 100
    provides_stream: bool = False
    execution_timeout: int = 120
    max_concurrent: int = 4
    settings_schema: dict[str, SettingsFieldSchema] = Field(default_factory=dict)
    actions: list[PluginAction] = Field(default_factory=list)


class PluginView(BaseModel):
    manifest: PluginManifest
    settings: dict[str, Any]
    health_status: HealthStatus = "unknown"


class ToggleRequest(BaseModel):
    is_active: bool


class SettingsUpdateRequest(BaseModel):
    settings: dict[str, Any]


class RegisterExternalRequest(BaseModel):
    manifest: PluginManifest
    endpoint_url: str


class HealthResponse(BaseModel):
    status: HealthStatus
    latency_ms: int | None = None


class PipelineTraceItem(BaseModel):
    plugin_id: str
    plugin_name: str
    duration_ms: int
    ok: bool
    error: str | None = None


class ChatResponse(BaseModel):
    response: str
    trace: list[PipelineTraceItem] = Field(default_factory=list)