from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_registry, require_admin
from ..interfaces.llm_spec import InferenceProvider
from ..models import User
from ..schemas import (
    PluginInfo,
    PluginSettingsResponse,
    PluginSettingsSave,
    PluginToggleRequest,
)
from ..services.plugin_loader import PluginRecord, PluginRegistry

logger = logging.getLogger("conturai.backend.admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _to_info(rec: PluginRecord) -> PluginInfo:
    return PluginInfo(
        id=rec.id,
        name=rec.plugin.name or rec.id,
        version=rec.plugin.version,
        type=rec.manifest.get("type", "local"),
        status=rec.status,
        error=rec.error,
        has_settings=rec.plugin.get_settings_blueprint() is not None,
        endpoint_url=rec.endpoint_url,
        is_inference_provider=isinstance(rec.plugin, InferenceProvider),
    )


@router.get("/plugins", response_model=List[PluginInfo])
async def list_plugins(
    _: User = Depends(require_admin),
    registry: PluginRegistry = Depends(get_registry),
):
    return [_to_info(rec) for rec in registry.list_all()]


@router.post("/plugins/{plugin_id}/toggle", response_model=PluginInfo)
async def toggle_plugin(
    plugin_id: str,
    payload: PluginToggleRequest,
    _: User = Depends(require_admin),
    registry: PluginRegistry = Depends(get_registry),
):
    rec = registry.get(plugin_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")

    try:
        if payload.active:
            await registry.activate_plugin(plugin_id)
        else:
            await registry.deactivate_plugin(plugin_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Plugin not found")
    except Exception as exc:
        # Плагин остаётся в статусе "error" — возвращаем 500 с деталями
        raise HTTPException(status_code=500, detail=str(exc))

    return _to_info(registry.get(plugin_id))


@router.get(
    "/plugins/{plugin_id}/config",
    response_model=PluginSettingsResponse,
    response_model_by_alias=True,
)
async def get_plugin_config(
    plugin_id: str,
    _: User = Depends(require_admin),
    registry: PluginRegistry = Depends(get_registry),
):
    rec = registry.get(plugin_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Plugin not found")

    blueprint = rec.plugin.get_settings_blueprint()
    if blueprint is None:
        raise HTTPException(
            status_code=404, detail="Plugin does not expose settings schema"
        )

    return PluginSettingsResponse(
        plugin_id=plugin_id,
        schema=blueprint.model_json_schema(),
        current=dict(rec.settings),
    )


@router.post(
    "/plugins/{plugin_id}/config",
    response_model=PluginSettingsResponse,
    response_model_by_alias=True,
)
async def save_plugin_config(
    plugin_id: str,
    payload: PluginSettingsSave,
    _: User = Depends(require_admin),
    registry: PluginRegistry = Depends(get_registry),
):
    rec = registry.get(plugin_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Plugin not found")

    blueprint = rec.plugin.get_settings_blueprint()
    if blueprint is None:
        raise HTTPException(
            status_code=404, detail="Plugin does not expose settings schema"
        )

    try:
        await registry.save_settings(plugin_id, payload.settings)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("save settings failed")
        raise HTTPException(status_code=500, detail=str(exc))

    return PluginSettingsResponse(
        plugin_id=plugin_id,
        schema=blueprint.model_json_schema(),
        current=dict(rec.settings),
    )