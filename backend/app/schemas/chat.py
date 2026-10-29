from __future__ import annotations

from pydantic import BaseModel, Field


class ChatCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class ChatOut(BaseModel):
    id: str
    title: str
    created_at: str


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class SendMessageRequest(BaseModel):
    plugin_id: str
    content: str = Field(..., min_length=1)


class SendMessageResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut