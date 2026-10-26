import asyncio
import re
from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymorphy3 import MorphAnalyzer
from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Document
from app.services import llm_config_service

_morph = MorphAnalyzer()

def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(_morph.normal_forms(w)[0] for w in cleaned.split())


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "(?<=\\.)!", " "],
        length_function=len,
    )
    return splitter.split_text(text)


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model_path)

@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    # Модель для пересортировки
    return CrossEncoder(settings.reranker_model_path)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    loop = asyncio.get_running_loop()
    model = get_model()

    def _encode() -> list[list[float]]:
        vectors = model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]

    return await loop.run_in_executor(None, _encode)


async def embed_one(text: str) -> list[float]:
    return (await embed_texts([text]))[0]

async def rerank_documents(query: str, docs: list[Document], top_n: int) -> list[Document]:
    if not docs:
        return []
    
    loop = asyncio.get_running_loop()
    model = get_reranker()
    pairs = [[query, doc.text] for doc in docs]
    
    def _predict():
        return model.predict(pairs)

    scores = await loop.run_in_executor(None, _predict)
    scored_docs = list(zip(docs, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    return [doc for doc, score in scored_docs[:top_n]]


async def add_document(
    session: AsyncSession,
    source: str,
    text: str,
    upload_id=None,
) -> int:
    cfg = await llm_config_service.get_rag(session)
    chunks = split_text(text, cfg["chunk_size"], cfg["chunk_overlap"])
    if not chunks:
        return 0

    points: list[Document] = []
    for i in range(0, len(chunks), cfg["batch_size"]):
        batch = chunks[i : i + cfg["batch_size"]]
        vectors = await embed_texts(batch)
        for j, (chunk, vector) in enumerate(zip(batch, vectors)):
            points.append(
                Document(
                    source=source,
                    text=chunk,
                    text_norm=normalize_text(chunk),
                    page=i + j + 1,
                    language="ru",
                    embedding=vector,
                    upload_id=upload_id,
                )
            )

    session.add_all(points)
    await session.commit()
    return len(points)


async def search_documents(
    session: AsyncSession,
    query: str,
    limit: int | None = None,
    tags: list[str] | None = None,
) -> list[Document]:
    if limit is None:
        cfg = await llm_config_service.get_rag(session)
        limit = cfg["search_limit"]

    query_vector = await embed_one(query)
    
    THRESHOLD = 0.4 

    stmt = (
        select(Document)
        .where(Document.embedding.cosine_distance(query_vector) < THRESHOLD)
    )

    if tags:
        from app.db.models import Upload
        stmt = stmt.join(Upload, Document.upload_id == Upload.id).where(
            Upload.tags.overlap(tags)
        )
    
    stmt = stmt.order_by(Document.embedding.cosine_distance(query_vector)).limit(limit * 2)

    result = await session.execute(stmt)
    candidates = list(result.scalars().all())
    
    # Пересортировываем и отдаем ровно limit
    return await rerank_documents(query, candidates, top_n=limit)


def format_context(docs: list[Document]) -> str:
    if not docs:
        return ""
    parts = [f"[{d.source}]\n{d.text}" for d in docs]
    return "\n\n---\n\n".join(parts)