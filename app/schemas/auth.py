from pydantic import BaseModel


class TokenResponse(BaseModel):
    result: bool = True
    access_token: str
    token_type: str = "bearer"
    message: str = "Авторизация прошла успешно"
    category: str = "success"