from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


UserRole = Literal["user", "editor", "admin"]


class LoginRequest(BaseModel):
    login: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserView(BaseModel):
    id: str
    login: str
    display_name: str | None
    role: UserRole
    is_active: bool


class UserCreateRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    display_name: str | None = None
    role: UserRole = "user"


class UpdateRoleRequest(BaseModel):
    role: UserRole


class UpdateActiveRequest(BaseModel):
    is_active: bool


class UpdatePasswordRequest(BaseModel):
    password: str = Field(..., min_length=6, max_length=128)


class ChangeMyPasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)