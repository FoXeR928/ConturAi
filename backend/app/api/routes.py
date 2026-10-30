from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.auth.deps import get_admin_user
from app.core.errors import ApiError
from app.schemas.plugin import (
    HealthResponse,
    PluginView,
    RegisterExternalRequest,
    SettingsUpdateRequest,
    ToggleRequest,
)


router = APIRouter(prefix="/api/v1", tags=["plugins"])


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
        return await _registry(request).toggle(plugin_id, payload.is_active)
    except KeyError as exc:
        raise ApiError("NOT_FOUND", str(exc), status=404) from exc


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
        raise ApiError("NOT_FOUND", str(exc), status=404) from exc
    except ValueError as exc:
        raise ApiError("VALIDATION_ERROR", str(exc), status=422) from exc


@router.post(
    "/plugins/register", response_model=PluginView, status_code=201,
)
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
        raise ApiError("VALIDATION_ERROR", str(exc), status=422) from exc


@router.delete("/plugins/{plugin_id}", status_code=204)
async def delete_plugin(
    plugin_id: str,
    request: Request,
    _: dict[str, Any] = Depends(get_admin_user),
) -> None:
    try:
        await _registry(request).delete(plugin_id)
    except KeyError as exc:
        raise ApiError("NOT_FOUND", str(exc), status=404) from exc
    except ValueError as exc:
        raise ApiError("CONFLICT", str(exc), status=409) from exc


@router.post(
    "/plugins/{plugin_id}/actions/{action_id}", status_code=200,
)
async def run_plugin_action(
    plugin_id: str,
    action_id: str,
    request: Request,
    _: dict[str, Any] = Depends(get_admin_user),
) -> dict[str, Any]:
    try:
        await _registry(request).run_action(plugin_id, action_id)
    except KeyError as exc:
        raise ApiError("NOT_FOUND", str(exc), status=404) from exc
    except ValueError as exc:
        raise ApiError("VALIDATION_ERROR", str(exc), status=422) from exc
    except Exception as exc:
        raise ApiError("ACTION_FAILED", str(exc), status=502) from exc
    return {"result": True, "action_id": action_id}


@router.get(
    "/plugins/{plugin_id}/health", response_model=HealthResponse,
)
async def plugin_health(
    plugin_id: str,
    request: Request,
    _: dict[str, Any] = Depends(get_admin_user),
) -> HealthResponse:
    try:
        ok, latency = await _registry(request).check_health(plugin_id)
    except KeyError as exc:
        raise ApiError("NOT_FOUND", str(exc), status=404) from exc
    return HealthResponse(
        status="ok" if ok else "down",
        latency_ms=latency,
    )