from pydantic import BaseModel


class TextAdd(BaseModel):
    name: str
    text: str


class MessageIn(BaseModel):
    text: str


class ChatCreate(BaseModel):
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