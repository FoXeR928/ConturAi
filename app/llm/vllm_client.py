from openai import AsyncOpenAI

from app.core.config import settings

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.vllm_base_url,
            api_key=settings.vllm_api_key,
            timeout=120.0,
        )
    return _client


async def chat_completion(messages: list[dict[str, str]]) -> str:
    client = get_client()
    response = await client.chat.completions.create(
        model=settings.vllm_model,
        messages=messages,
        temperature=settings.vllm_temperature,
        max_tokens=settings.vllm_max_tokens,
        stream=False,
    )
    return response.choices[0].message.content or ""