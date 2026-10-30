from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from app.auth.deps import get_current_user
from app.core.errors import ApiError


router = APIRouter(prefix="/api/v1/plugins", tags=["plugins-proxy"])

_PROXY_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
_HOP_BY_HOP = {
    "host", "content-length", "transfer-encoding", "connection",
    "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "upgrade",
}


@router.api_route("/{plugin_id}/{path:path}", methods=_PROXY_METHODS)
async def proxy_plugin(
    plugin_id: str,
    path: str,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
) -> Response:
    registry = request.app.state.registry
    client = request.app.state.http_client

    plugin = registry.get(plugin_id)
    if plugin is None:
        raise ApiError("NOT_FOUND", "Плагин не найден", status=404)
    manifest = plugin.get_manifest()
    if manifest.kind != "external":
        raise ApiError(
            "BAD_REQUEST",
            "Проксирование доступно только для external-плагинов",
            status=400,
        )
    if not manifest.is_active:
        raise ApiError("PLUGIN_INACTIVE", "Плагин отключен", status=409)

    endpoint = registry.get_endpoint(plugin_id)
    if not endpoint:
        raise ApiError(
            "PLUGIN_ERROR", "У плагина не задан endpoint_url", status=502,
        )

    target = f"{endpoint.rstrip('/')}/{path}" if path else endpoint
    if request.url.query:
        target = f"{target}?{request.url.query}"

    headers = {
        name: value
        for name, value in request.headers.items()
        if name.lower() not in _HOP_BY_HOP
    }
    headers["X-User-Login"] = user["login"]
    headers["X-User-Role"] = user["role"]
    headers["X-User-Id"] = user["id"]

    body = await request.body()

    try:
        upstream = await client.request(
            method=request.method,
            url=target,
            headers=headers,
            content=body if body else None,
            timeout=float(manifest.execution_timeout),
        )
    except Exception as exc:
        raise ApiError(
            "PLUGIN_UNREACHABLE",
            f"Плагин недоступен: {exc}",
            status=502,
        ) from exc

    passthrough = {
        name: value
        for name, value in upstream.headers.items()
        if name.lower() not in _HOP_BY_HOP
    }

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=passthrough,
        media_type=upstream.headers.get("content-type"),
    )