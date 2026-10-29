from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth.deps import get_current_user
from app.auth.security import create_access_token, verify_password
from app.schemas.auth import LoginRequest, TokenResponse, UserView


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, request: Request,
) -> TokenResponse:
    user_store = request.app.state.user_store
    user = await user_store.get_by_login(payload.login)
    if user is None or not user["is_active"]:
        raise HTTPException(
            status_code=401, detail="Неверный логин или пароль",
        )
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=401, detail="Неверный логин или пароль",
        )
    token = create_access_token(user["login"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserView)
async def me(
    user: dict[str, Any] = Depends(get_current_user),
) -> UserView:
    return UserView(
        id=user["id"],
        login=user["login"],
        display_name=user.get("display_name"),
        role=user["role"],
    )