from pydantic import BaseModel


class MessageIn(BaseModel):
    text: str


class ChatCreate(BaseModel):
    name: str