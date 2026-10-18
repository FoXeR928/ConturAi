import asyncio
import re
from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymorphy3 import MorphAnalyzer
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Document

_morph = MorphAnalyzer()


# ---------- Чанкинг ----------
def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(_morph.normal_forms(w)[0] for w in cleaned.split())


def split_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=["\n\n", "\n", "(?<=\\.)!", " "],
        length_function=len,
    )
    return splitter.split_text(text)


# ---------- Эмбеддинги ----------
@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model_path)


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


# ---------- Хранилище ----------
async def add_document(session: AsyncSession, source: str, text: str) -> int:
    chunks = split_text(text)
    if not chunks:
        return 0

    points: list[Document] = []
    for i in range(0, len(chunks), settings.rag_batch_size):
        batch = chunks[i : i + settings.rag_batch_size]
        vectors = await embed_texts(batch)
        
        for j, (chunk, vector) in enumerate(zip(batch, vectors)):
            chunk_norm = normalize_text(chunk)
            
            points.append(
                Document(
                    source=source,
                    text=chunk,
                    text_norm=chunk_norm,
                    page=i + j + 1,
                    language="ru",
                    embedding=vector,
                )
            )

    session.add_all(points)
    await session.commit()
    return len(points)

async def search_documents(
    session: AsyncSession, query: str, limit: int | None = None
) -> list[Document]:
    limit = limit or settings.rag_search_limit
    query_vector = await embed_one(query)
    stmt = (
        select(Document)
        .order_by(Document.embedding.cosine_distance(query_vector))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def format_context(docs: list[Document]) -> str:
    if not docs:
        return ""
    return "\n---\n".join(d.text[:500] for d in docs)