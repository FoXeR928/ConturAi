from pydantic import BaseModel


class TextAdd(BaseModel):
    name: str
    text: str