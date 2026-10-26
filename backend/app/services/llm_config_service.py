from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models import LlmConfig


DEFAULT_LLM_CONFIGS: dict[str, dict[str, str]] = {
    # --- vLLM connection ---
    "vllm_base_url": {
        "value": "http://vllm:8000/v1",
        "description": "OpenAI-совместимый URL vLLM",
        "input_type": "text",
    },
    "vllm_api_key": {
        "value": "EMPTY",
        "description": "API-ключ vLLM (обычно EMPTY)",
        "input_type": "text",
        "is_secret": True,
    },
    "vllm_model_name": {
        "value": "local-model",
        "description": "Имя модели, с которым vLLM запущен (--served-model-name)",
        "input_type": "text",
    },

    # --- Sampling ---
    "vllm_temperature": {
        "value": "0.7",
        "description": "Температура (0.0–2.0). 0 = детерминированно, 1+ = креативно",
        "input_type": "float",
    },
    "vllm_max_tokens": {
        "value": "2048",
        "description": "Максимальное число токенов в ответе",
        "input_type": "number",
    },
    "vllm_top_p": {
        "value": "1.0",
        "description": "Nucleus sampling: 1.0 = выкл, 0.9 = топ 90% вероятностей",
        "input_type": "float",
    },
    "vllm_top_k": {
        "value": "-1",
        "description": "Top-K sampling: -1 = выкл",
        "input_type": "number",
    },
    "vllm_presence_penalty": {
        "value": "0.0",
        "description": "Штраф за повторение темы (-2.0 … 2.0)",
        "input_type": "float",
    },
    "vllm_frequency_penalty": {
        "value": "0.0",
        "description": "Штраф за частоту токенов (-2.0 … 2.0)",
        "input_type": "float",
    },
    "vllm_seed": {
        "value": "",
        "description": "Seed для воспроизводимости (пусто = случайно)",
        "input_type": "text",
    },

    # --- RAG ---
    "rag_search_limit": {
        "value": "5",
        "description": "Сколько чанков отдавать LLM (1–10)",
        "input_type": "number",
    },
    "rag_chunk_size": {
        "value": "800",
        "description": "Размер чанка в символах (применяется к НОВЫМ документам)",
        "input_type": "number",
    },
    "rag_chunk_overlap": {
        "value": "100",
        "description": "Перекрытие чанков в символах",
        "input_type": "number",
    },
    "rag_batch_size": {
        "value": "64",
        "description": "Сколько чанков эмбеддить за раз",
        "input_type": "number",
    },
    "rag_history_limit": {
        "value": "20",
        "description": "Сколько последних сообщений загружать в контекст (1-50)",
        "input_type": "number",
    },

    # --- JWT ---
    "token_expire_minutes": {
        "value": "30",
        "description": "Время жизни обычного JWT-токена (минуты)",
        "input_type": "number",
    },
    "token_expire_days": {
        "value": "7",
        "description": "Время жизни «долгого» JWT-токена (дни)",
        "input_type": "number",
    },
}


async def list_configs(session: AsyncSession) -> list[dict]:
    result = await session.execute(select(LlmConfig))
    configs = []
    for c in result.scalars().all():
        val = c.value
        if c.is_secret and val:
            val = "********"
        configs.append({
            "key": c.key,
            "value": val,
            "description": c.description,
            "input_type": c.input_type,
            "is_secret": c.is_secret
        })
    return configs

async def get_all(session: AsyncSession) -> dict[str, str]:
    result = await session.execute(select(LlmConfig.key, LlmConfig.value, LlmConfig.is_secret))
    out = {}
    for k, v, is_secret in result.all():
        if is_secret:
            out[k] = decrypt_secret(v)
        else:
            out[k] = v
    return out

async def get_typed(session: AsyncSession) -> dict[str, Any]:
    raw = await get_all(session)
    seed_raw = raw.get("vllm_seed", "").strip()
    return {
        # подключение
        "base_url": raw.get("vllm_base_url", "http://vllm:8000/v1"),
        "api_key": raw.get("vllm_api_key", "EMPTY"),
        "model": raw.get("vllm_model_name", "local-model"),
        # sampling
        "temperature": float(raw.get("vllm_temperature", "0.7")),
        "max_tokens": int(raw.get("vllm_max_tokens", "2048")),
        "top_p": float(raw.get("vllm_top_p", "1.0")),
        "top_k": int(raw.get("vllm_top_k", "-1")),
        "presence_penalty": float(raw.get("vllm_presence_penalty", "0.0")),
        "frequency_penalty": float(raw.get("vllm_frequency_penalty", "0.0")),
        "seed": int(seed_raw) if seed_raw else None,
    }


async def get_rag(session: AsyncSession) -> dict[str, int]:
    raw = await get_all(session)
    return {
        "search_limit": int(raw.get("rag_search_limit", "5")),
        "chunk_size": int(raw.get("rag_chunk_size", "800")),
        "chunk_overlap": int(raw.get("rag_chunk_overlap", "100")),
        "batch_size": int(raw.get("rag_batch_size", "64")),
        "history_limit": int(raw.get("rag_history_limit", "20")),
    }


async def get_jwt(session: AsyncSession) -> dict[str, int]:
    raw = await get_all(session)
    return {
        "minutes": int(raw.get("token_expire_minutes", "30")),
        "days": int(raw.get("token_expire_days", "7")),
    }


async def update_config(session: AsyncSession, key: str, value: str) -> None:
    config = (await session.execute(select(LlmConfig).where(LlmConfig.key == key))).scalar_one_or_none()
    if not config:
        raise AppError(f"Параметр '{key}' не найден", "warning", 404)

    final_value = str(value)
    if config.is_secret and final_value != "********":
        final_value = encrypt_secret(final_value)

    await session.execute(
        update(LlmConfig).where(LlmConfig.key == key).values(value=final_value)
    )
    await session.commit()


async def seed_defaults(session: AsyncSession) -> None:
    for key, meta in DEFAULT_LLM_CONFIGS.items():
        exists = (await session.execute(select(LlmConfig.id).where(LlmConfig.key == key))).scalar_one_or_none()
        if exists is None:
            session.add(
                LlmConfig(
                    key=key,
                    value=meta["value"],
                    description=meta["description"],
                    input_type=meta["input_type"],
                    is_secret=meta.get("is_secret", False),
                )
            )
    await session.commit()