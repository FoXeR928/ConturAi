from pydantic import BaseModel
from uuid import UUID
from typing import List, Literal

class TextAdd(BaseModel):
    name: str
    text: str
    upload_id: UUID | None = None
    tags: List[str] = []

class MessageIn(BaseModel):
    text: str
    tags: List[str] = [] # <-- Важно

class ChatCreate(BaseModel):
    name: str

class ChatRename(BaseModel):
    name: str

class RegistrationUser(BaseModel):
    login: str
    user_name: str
    password: str

class UpdatePassword(BaseModel):
    login: str
    password: str

class UpdateRole(BaseModel):
    login: str
    is_admin: bool

class UpdateStatus(BaseModel):
    login: str
    disabled: bool

class PromptUpdate(BaseModel):
    key: str
    value: str

class LlmConfigUpdate(BaseModel):
    key: str
    value: str

class FewShotCreate(BaseModel):
    question: str
    answer: str
class DownloadRequestCreate(BaseModel):
    upload_id: UUID

class DownloadRequestAction(BaseModel):
    request_id: UUID
    action: Literal["approve", "reject"]
