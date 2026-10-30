from __future__ import annotations

from typing import Any

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from app.auth.security import decode_access_token
from app.core.errors import ApiError


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", auto_error=False,
)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
) -> dict[str, Any]:
    if not token:
        raise ApiError("UNAUTHORIZED", "Требуется авторизация", status=401)
    try:
        login = decode_access_token(token)
    except Exception:
        raise ApiError("UNAUTHORIZED", "Неверный токен", status=401) from None
    user_store = request.app.state.user_store
    user = await user_store.get_by_login(login)
    if user is None or not user["is_active"]:
        raise ApiError("UNAUTHORIZED", "Пользователь не найден", status=401)
    return user


async def get_admin_user(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if user["role"] != "admin":
        raise ApiError("FORBIDDEN", "Только для администратора", status=403)
    return user


async def get_editor_user(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if user["role"] not in ("admin", "editor"):
        raise ApiError("FORBIDDEN", "Требуется роль editor или admin", status=403)
    return user