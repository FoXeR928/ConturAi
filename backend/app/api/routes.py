from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth.deps import get_admin_user
from app.schemas.plugin import (
    PluginView,
    RegisterExternalRequest,
    SettingsUpdateRequest,
    ToggleRequest,
)


router = APIRouter(prefix="/api", tags=["plugins"])


def _registry(request: Request):
    return request.app.state.registry


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/plugins", response_model=list[PluginView])
async def list_plugins(
    request: Request,
    _: dict[str, Any] = Depends(get_admin_user),
) -> list[PluginView]:
    return _registry(request).list_views()


@router.patch("/plugins/{plugin_id}/toggle", response_model=PluginView)
async def toggle_plugin(
    plugin_id: str,
    payload: ToggleRequest,
    request: Request,
    _: dict[str, Any] = Depends(get_admin_user),
) -> PluginView:
    try:
        return await _registry(request).toggle(
            plugin_id, payload.is_active,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/plugins/{plugin_id}/settings", response_model=PluginView)
async def update_settings(
    plugin_id: str,
    payload: SettingsUpdateRequest,
    request: Request,
    _: dict[str, Any] = Depends(get_admin_user),
) -> PluginView:
    try:
        return await _registry(request).update_settings(
            plugin_id, payload.settings,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/plugins/register", response_model=PluginView, status_code=201)
async def register_external(
    payload: RegisterExternalRequest,
    request: Request,
    _: dict[str, Any] = Depends(get_admin_user),
) -> PluginView:
    try:
        return await _registry(request).register_external(
            payload.manifest, payload.endpoint_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc