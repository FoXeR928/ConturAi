from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator

import httpx

from app.plugins.context import PluginSystemContext
from app.schemas.plugin import PipelineContext


logger = logging.getLogger("conturai.plugin.llm_vllm")

_http: httpx.AsyncClient | None = None
_docker: Any = None
_network: str = "conturai_conturai"


def configure(ctx: PluginSystemContext) -> None:
    global _http, _docker, _network
    _http = ctx.http_client
    _docker = ctx.docker_client
    _network = ctx.docker_network or "conturai_conturai"
    logger.info(
        "llm_vllm configured: docker=%s, network=%s",
        _docker is not None, _network,
    )


async def check_health(settings: dict[str, Any]) -> bool:
    try:
        url = _resolve_base_url(settings)
        if not url or not _http:
            return False
        response = await _http.get(f"{url}/v1/models", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


async def shutdown() -> None:
    return None


def _resolve_base_url(settings: dict[str, Any]) -> str | None:
    mode = str(settings.get("mode", "external"))
    if mode == "external":
        return str(settings.get("external_url", "")).rstrip("/") or None
    container_name = str(settings.get("container_name", "conturai_plugin_vllm"))
    return f"http://{container_name}:8000"


def _build_command(settings: dict[str, Any]) -> list[str]:
    model = str(settings.get("model", "Qwen/Qwen2.5-1.5B-Instruct"))
    served = str(settings.get("served_model_name", "local-model"))
    max_len = int(settings.get("max_model_len", 2048))
    return [
        "--model", model,
        "--served-model-name", served,
        "--max-model-len", str(max_len),
        "--gpu-memory-utilization", "0.85",
    ]


async def _run_blocking(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


async def _ensure_container(settings: dict[str, Any]) -> None:
    if _docker is None:
        raise RuntimeError(
            "Docker SDK недоступен — managed-режим не поддерживается. "
            "Проверьте, что /var/run/docker.sock смонтирован в backend."
        )

    container_name = str(settings.get("container_name", "conturai_plugin_vllm"))
    desired_model = str(settings.get("model", "Qwen/Qwen2.5-1.5B-Instruct"))
    image = str(settings.get("image", "vllm/vllm-openai:latest"))
    host_port = int(settings.get("host_port", 8000))
    gpu = bool(settings.get("gpu_enabled", True))
    hf_token = str(settings.get("hf_token", ""))

    def _check_and_create() -> str:
        try:
            container = _docker.containers.get(container_name)
            labels = container.labels or {}
            current_model = labels.get("conturai.model")
            if container.status != "running" or current_model != desired_model:
                logger.info(
                    "[managed] recreating %s (was model=%s, status=%s)",
                    container_name, current_model, container.status,
                )
                try:
                    container.remove(force=True)
                except Exception:
                    pass
                raise LookupError("recreate")
            logger.info("[managed] %s already running", container_name)
            return "existing"
        except LookupError:
            raise
        except Exception:
            # NotFound
            pass

        logger.info(
            "[managed] creating %s (model=%s)", container_name, desired_model,
        )
        run_kwargs: dict[str, Any] = {
            "image": image,
            "name": container_name,
            "detach": True,
            "ports": {"8000/tcp": host_port},
            "environment": {"HUGGING_FACE_HUB_TOKEN": hf_token} if hf_token else {},
            "command": _build_command(settings),
            "labels": {
                "conturai.plugin": "llm_vllm",
                "conturai.model": desired_model,
            },
            "network": _network,
            "ipc_mode": "host",
            "restart_policy": {"Name": "unless-stopped"},
        }
        if gpu:
            run_kwargs["device_requests"] = [
                {"count": -1, "capabilities": [["gpu"]]},
            ]
        _docker.containers.run(**run_kwargs)
        return "created"

    try:
        await _run_blocking(_check_and_create)
    except LookupError:
        await _run_blocking(_check_and_create)

    await _wait_ready(_resolve_base_url(settings), timeout=900)


async def _wait_ready(url: str | None, timeout: int) -> None:
    if not url or not _http:
        raise RuntimeError("URL vLLM не задан")
    start = time.monotonic()
    last_err = ""
    while time.monotonic() - start < timeout:
        try:
            r = await _http.get(f"{url}/v1/models", timeout=5.0)
            if r.status_code == 200:
                logger.info("[managed] vLLM ready at %s", url)
                return
            last_err = f"HTTP {r.status_code}"
        except Exception as exc:
            last_err = str(exc)
        await asyncio.sleep(3)
    raise RuntimeError(
        f"vLLM не поднялся за {timeout}s: {last_err}"
    )


def _build_messages(ctx: PipelineContext) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for m in ctx.history:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": ctx.prompt})
    return messages


def _base_payload(ctx: PipelineContext, settings: dict[str, Any], stream: bool) -> dict[str, Any]:
    return {
        "model": str(settings.get("served_model_name", "local-model")),
        "messages": _build_messages(ctx),
        "temperature": float(settings.get("temperature", 0.7)),
        "max_tokens": int(settings.get("max_tokens", 1024)),
        "stream": stream,
    }


async def handle(
    ctx: PipelineContext, settings: dict[str, Any],
) -> PipelineContext:
    mode = str(settings.get("mode", "external"))
    if mode == "managed":
        await _ensure_container(settings)

    url = _resolve_base_url(settings)
    if not url or not _http:
        raise RuntimeError("vLLM URL не настроен")

    payload = _base_payload(ctx, settings, stream=False)
    response = await _http.post(
        f"{url}/v1/chat/completions",
        json=payload,
        timeout=float(settings.get("max_tokens", 1024)) + 120,
    )
    response.raise_for_status()
    data = response.json()
    answer = data["choices"][0]["message"]["content"]
    ctx.answer = answer
    ctx.metadata["llm_used"] = True
    ctx.metadata["llm_model"] = payload["model"]
    return ctx


async def handle_stream(
    ctx: PipelineContext, settings: dict[str, Any],
) -> AsyncGenerator[str, None]:
    mode = str(settings.get("mode", "external"))
    if mode == "managed":
        await _ensure_container(settings)

    url = _resolve_base_url(settings)
    if not url or not _http:
        raise RuntimeError("vLLM URL не настроен")

    payload = _base_payload(ctx, settings, stream=True)

    async with _http.stream(
        "POST", f"{url}/v1/chat/completions",
        json=payload, timeout=None,
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue
            raw = line[6:]
            if raw == "[DONE]":
                break
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            choice = obj.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            content = delta.get("content")
            if content:
                ctx.answer = (ctx.answer or "") + content
                yield content

    ctx.metadata["llm_used"] = True
    ctx.metadata["llm_model"] = payload["model"]


async def reconfigure(settings: dict[str, Any]) -> None:
    """Вызывается после update_settings. Если managed — пересоздаём контейнер
    при изменении модели/образа; если external — останавливаем контейнер,
    если он был создан ранее (переключились с managed)."""
    mode = str(settings.get("mode", "external"))
    if _docker is None:
        return

    container_name = str(settings.get("container_name", "conturai_plugin_vllm"))

    if mode == "external":
        def _stop_if_exists() -> None:
            try:
                c = _docker.containers.get(container_name)
                logger.info("[reconfigure] stopping %s (switched to external)", container_name)
                try:
                    c.stop(timeout=15)
                except Exception:
                    pass
            except Exception:
                pass
        await _run_blocking(_stop_if_exists)
        return

    # managed: пересоздать при изменении модели/образа
    def _recreate() -> None:
        try:
            c = _docker.containers.get(container_name)
            labels = c.labels or {}
            if (
                labels.get("conturai.model") != str(settings.get("model"))
                or c.attrs["Config"]["Image"].split(":")[0]
                != str(settings.get("image", "")).split(":")[0]
            ):
                logger.info("[reconfigure] removing %s for recreate", container_name)
                try:
                    c.remove(force=True)
                except Exception:
                    pass
        except Exception:
            pass

    await _run_blocking(_recreate)
    # сам контейнер поднимется при следующем execute()


# ==========================================================================
# Actions (кнопки в UI)
# ==========================================================================

async def handle_action_restart() -> None:
    if _docker is None:
        raise RuntimeError("Docker SDK недоступен")
    def _rm():
        # Достаём имя из состояния — плагин не получает settings в action API;
        # для MVP используем дефолт. В следующей итерации можно расширить.
        name = "conturai_plugin_vllm"
        try:
            c = _docker.containers.get(name)
            c.remove(force=True)
        except Exception:
            pass
    await _run_blocking(_rm)


async def handle_action_stop() -> None:
    if _docker is None:
        raise RuntimeError("Docker SDK недоступен")
    def _stop():
        name = "conturai_plugin_vllm"
        try:
            c = _docker.containers.get(name)
            c.stop(timeout=15)
        except Exception:
            pass
    await _run_blocking(_stop)