from pydantic import BaseModel


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