from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


FieldType = Literal["select", "slider", "number", "text", "boolean"]
HealthStatus = Literal["ok", "down", "unknown"]
PluginKind = Literal["internal", "external"]


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


class PluginManifest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_\-]+$")
    name: str
    description: str = ""
    version: str = "1.0.0"
    api_version: str = "1"
    kind: PluginKind
    is_active: bool = True
    streaming: bool = False
    max_history_chars: int = 8000
    execution_timeout: int = 120
    max_concurrent: int = 4
    settings_schema: dict[str, SettingsFieldSchema] = Field(default_factory=dict)


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


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class HealthResponse(BaseModel):
    status: HealthStatus
    latency_ms: int | None = None