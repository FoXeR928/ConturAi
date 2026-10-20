from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models import LlmConfig


# Значения по умолчанию — используются при первом запуске
DEFAULT_LLM_CONFIGS: dict[str, dict[str, str]] = {
    "vllm_base_url": {
        "value": "http://vllm:8000/v1",
        "description": "OpenAI-совместимый URL vLLM",
        "input_type": "text",
    },
    "vllm_api_key": {
        "value": "EMPTY",
        "description": "API-ключ vLLM (обычно EMPTY)",
        "input_type": "text",
    },
    "vllm_model_name": {
        "value": "local-model",
        "description": "Имя модели, с которым vLLM запущен (--served-model-name)",
        "input_type": "text",
    },
    "vllm_temperature": {
        "value": "0.7",
        "description": "Температура генерации (0.0–2.0)",
        "input_type": "float",
    },
    "vllm_max_tokens": {
        "value": "2048",
        "description": "Максимальное число токенов в ответе",
        "input_type": "number",
    },
}


async def list_configs(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(
            LlmConfig.key,
            LlmConfig.value,
            LlmConfig.description,
            LlmConfig.input_type,
            LlmConfig.updated_at,
        )
    )
    return [dict(r._mapping) for r in result.all()]


async def get_all(session: AsyncSession) -> dict[str, str]:
    result = await session.execute(select(LlmConfig.key, LlmConfig.value))
    return {k: v for k, v in result.all()}


async def get_typed(session: AsyncSession) -> dict[str, Any]:
    raw = await get_all(session)
    return {
        "base_url": raw.get("vllm_base_url", "http://vllm:8000/v1"),
        "api_key": raw.get("vllm_api_key", "EMPTY"),
        "model": raw.get("vllm_model_name", "local-model"),
        "temperature": float(raw.get("vllm_temperature", "0.7")),
        "max_tokens": int(raw.get("vllm_max_tokens", "2048")),
    }


async def update_config(session: AsyncSession, key: str, value: str) -> None:
    exists = (
        await session.execute(select(LlmConfig.id).where(LlmConfig.key == key))
    ).scalar_one_or_none()
    if not exists:
        raise AppError(f"Параметр LLM '{key}' не найден", "warning", 404)
    await session.execute(
        update(LlmConfig).where(LlmConfig.key == key).values(value=str(value))
    )
    await session.commit()


async def seed_defaults(session: AsyncSession) -> None:
    for key, meta in DEFAULT_LLM_CONFIGS.items():
        exists = (
            await session.execute(select(LlmConfig.id).where(LlmConfig.key == key))
        ).scalar_one_or_none()
        if exists is None:
            session.add(
                LlmConfig(
                    key=key,
                    value=meta["value"],
                    description=meta["description"],
                    input_type=meta["input_type"],
                )
            )
    await session.commit()