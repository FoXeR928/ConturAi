import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def get_embedding_dim() -> int:
    return get_model().get_sentence_embedding_dimension()


async def embed_texts(texts: list[str]) -> list[list[float]]:
    loop = asyncio.get_running_loop()
    model = get_model()

    def _encode() -> list[list[float]]:
        vectors = model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]

    return await loop.run_in_executor(None, _encode)


async def embed_one(text: str) -> list[float]:
    return (await embed_texts([text]))[0]