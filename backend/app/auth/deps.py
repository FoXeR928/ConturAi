from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from app.auth.security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login", auto_error=False,
)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
) -> dict[str, Any]:
    if not token:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        login = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Неверный токен") from None
    user_store = request.app.state.user_store
    user = await user_store.get_by_login(login)
    if user is None or not user["is_active"]:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user


async def get_admin_user(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if user["role"] != "admin":
        raise HTTPException(
            status_code=403, detail="Доступ только для администратора",
        )
    return user