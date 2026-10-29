from pydantic import BaseModel
from typing import Literal

# ==============================================================================
# БЛОК 1: ЧАТЫ И СООБЩЕНИЯ
# ==============================================================================

class ChatCreate(BaseModel):
    name: str

class ChatRename(BaseModel):
    name: str

class MessageIn(BaseModel):
    text: str


# ==============================================================================
# БЛОК 2: ПОЛЬЗОВАТЕЛИ И БЕЗОПАСНОСТЬ
# ==============================================================================

class RegistrationUser(BaseModel):
    login: str
    user_name: str
    password: str
    role: Literal["user", "editor", "admin"] = "user" 

class UpdatePassword(BaseModel):
    login: str
    password: str

class UpdateRole(BaseModel):
    login: str
    role: Literal["user", "editor", "admin"]

class UpdateStatus(BaseModel):
    login: str
    disabled: bool

class UpdateUserName(BaseModel):
    login: str
    user_name: str