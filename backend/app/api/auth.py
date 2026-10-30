from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.auth.deps import get_current_user
from app.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.core.errors import ApiError
from app.core.ratelimit import limiter
from app.schemas.auth import (
    ChangeMyPasswordRequest,
    LoginRequest,
    TokenResponse,
    UserView,
)


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request) -> TokenResponse:
    ip = request.client.host if request.client else "unknown"
    limiter.hit(
        f"login:{ip}",
        settings.login_rate_limit,
        settings.login_window_seconds,
    )
    user_store = request.app.state.user_store
    user = await user_store.get_by_login(payload.login)
    if user is None or not user["is_active"]:
        raise ApiError("UNAUTHORIZED", "Неверный логин или пароль", status=401)
    if not verify_password(payload.password, user["password_hash"]):
        raise ApiError("UNAUTHORIZED", "Неверный логин или пароль", status=401)
    return TokenResponse(access_token=create_access_token(user["login"]))


@router.get("/me", response_model=UserView)
async def me(user: dict[str, Any] = Depends(get_current_user)) -> UserView:
    return UserView(
        id=user["id"],
        login=user["login"],
        display_name=user.get("display_name"),
        role=user["role"],
        is_active=user["is_active"],
    )


@router.patch("/me/password", status_code=204)
async def change_my_password(
    payload: ChangeMyPasswordRequest,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> None:
    user_store = request.app.state.user_store
    full = await user_store.get_by_id(user["id"])
    if full is None:
        raise ApiError("NOT_FOUND", "Пользователь не найден", status=404)
    if not verify_password(payload.old_password, full["password_hash"]):
        raise ApiError("FORBIDDEN", "Неверный текущий пароль", status=403)
    await user_store.update_password(
        user["id"], hash_password(payload.new_password),
    )