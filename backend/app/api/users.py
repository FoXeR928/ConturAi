from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.auth.deps import get_admin_user
from app.auth.security import hash_password
from app.core.errors import ApiError
from app.schemas.auth import (
    UpdateActiveRequest,
    UpdatePasswordRequest,
    UpdateRoleRequest,
    UserCreateRequest,
    UserView,
)


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=list[UserView])
async def list_users(
    request: Request,
    _: dict[str, Any] = Depends(get_admin_user),
) -> list[UserView]:
    store = request.app.state.user_store
    rows = await store.list_all()
    return [UserView(**r) for r in rows]


@router.post("", response_model=UserView, status_code=201)
async def create_user(
    payload: UserCreateRequest,
    request: Request,
    _: dict[str, Any] = Depends(get_admin_user),
) -> UserView:
    store = request.app.state.user_store
    if await store.get_by_login(payload.login) is not None:
        raise ApiError("CONFLICT", "Логин уже занят", status=409)
    user_id = await store.create(
        login=payload.login,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role=payload.role,
    )
    return UserView(
        id=user_id,
        login=payload.login,
        display_name=payload.display_name,
        role=payload.role,
        is_active=True,
    )


@router.patch("/{user_id}/role", response_model=UserView)
async def update_role(
    user_id: str,
    payload: UpdateRoleRequest,
    request: Request,
    current: dict[str, Any] = Depends(get_admin_user),
) -> UserView:
    store = request.app.state.user_store
    target = await store.get_by_id(user_id)
    if target is None:
        raise ApiError("NOT_FOUND", "Пользователь не найден", status=404)
    if (
        target["role"] == "admin"
        and payload.role != "admin"
        and target["is_active"]
    ):
        if await store.count_active_admins() <= 1:
            raise ApiError(
                "CONFLICT",
                "Нельзя понизить последнего активного администратора",
                status=409,
            )
    await store.update_role(user_id, payload.role)
    target["role"] = payload.role
    return UserView(**{**target, "password_hash": ""})


@router.patch("/{user_id}/active", response_model=UserView)
async def update_active(
    user_id: str,
    payload: UpdateActiveRequest,
    request: Request,
    current: dict[str, Any] = Depends(get_admin_user),
) -> UserView:
    store = request.app.state.user_store
    target = await store.get_by_id(user_id)
    if target is None:
        raise ApiError("NOT_FOUND", "Пользователь не найден", status=404)
    if (
        target["role"] == "admin"
        and not payload.is_active
        and target["is_active"]
    ):
        if await store.count_active_admins() <= 1:
            raise ApiError(
                "CONFLICT",
                "Нельзя заблокировать последнего активного администратора",
                status=409,
            )
    await store.update_active(user_id, payload.is_active)
    target["is_active"] = payload.is_active
    return UserView(**{**target, "password_hash": ""})


@router.patch("/{user_id}/password", status_code=204)
async def update_password(
    user_id: str,
    payload: UpdatePasswordRequest,
    request: Request,
    _: dict[str, Any] = Depends(get_admin_user),
) -> None:
    store = request.app.state.user_store
    if await store.get_by_id(user_id) is None:
        raise ApiError("NOT_FOUND", "Пользователь не найден", status=404)
    await store.update_password(user_id, hash_password(payload.password))


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    request: Request,
    current: dict[str, Any] = Depends(get_admin_user),
) -> None:
    store = request.app.state.user_store
    target = await store.get_by_id(user_id)
    if target is None:
        raise ApiError("NOT_FOUND", "Пользователь не найден", status=404)
    if target["id"] == current["id"]:
        raise ApiError("CONFLICT", "Нельзя удалить самого себя", status=409)
    if target["role"] == "admin" and target["is_active"]:
        if await store.count_active_admins() <= 1:
            raise ApiError(
                "CONFLICT",
                "Нельзя удалить последнего активного администратора",
                status=409,
            )
    await store.delete(user_id)