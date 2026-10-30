from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---- Auth -----------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: UUID
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    role: str = "user"


# ---- Chats ----------------------------------------------------------------

class ChatRoomCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)


class ChatRoomRead(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)


class MessageRead(BaseModel):
    id: UUID
    room_id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Admin / Plugins ------------------------------------------------------

class PluginInfo(BaseModel):
    id: str
    name: str
    version: str
    type: str  # "local" | "remote"
    status: str  # "inactive" | "active" | "error"
    error: Optional[str] = None
    has_settings: bool = False
    endpoint_url: Optional[str] = None
    is_inference_provider: bool = False


class PluginToggleRequest(BaseModel):
    active: bool


class PluginSettingsResponse(BaseModel):
    plugin_id: str
    schema_: Dict[str, Any] = Field(alias="schema")
    current: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class PluginSettingsSave(BaseModel):
    settings: Dict[str, Any]