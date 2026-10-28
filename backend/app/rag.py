import asyncio
import re
from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymorphy3 import MorphAnalyzer
from sentence_transformers import SentenceTransformer, CrossEncoder

# ДОБАВЛЕНЫ НЕДОСТАЮЩИЕ ИМПОРТЫ ДЛЯ ТЕГОВ
from sqlalchemy import select, func, cast, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Document, Upload
from app.services import llm_config_service

# ==============================================================================
# БЛОК 1: НОРМАЛИЗАЦИЯ ТЕКСТА (ДЛЯ ПОИСКА)
# ==============================================================================

_morph = MorphAnalyzer()

def normalize_text(text: str) -> str:
    """
    Очищает текст от знаков препинания и приводит слова к леммам.
    Используется для точного текстового поиска (Full-Text Search).
    """
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(_morph.normal_forms(w)[0] for w in cleaned.split())


# ==============================================================================
# БЛОК 2: НАРЕЗКА ТЕКСТА НА ЧАНКИ
# ==============================================================================

def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Разбивает большой текст на небольшие куски (чанки) для индексации.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "(?<=\\.)!", " "],
        length_function=len,
    )
    return splitter.split_text(text)


# ==============================================================================
# БЛОК 3: ЛЕНИВАЯ ЗАГРУЗКА МОДЕЛЕЙ (ЭМБЕДДИНГИ И РЕРАНКЕР)
# ==============================================================================

@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model_path, device="cpu")

@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    return CrossEncoder(settings.reranker_model_path, device="cpu")


# ==============================================================================
# БЛОК 4: ГЕНЕРАЦИЯ ЭМБЕДДИНГОВ (ВЕКТОРОВ)
# ==============================================================================

async def embed_texts(texts: list[str]) -> list[list[float]]:
    loop = asyncio.get_running_loop()
    model = get_model()

    def _encode() -> list[list[float]]:
        vectors = model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]

    return await loop.run_in_executor(None, _encode)

async def embed_one(text: str) -> list[float]:
    return (await embed_texts([text]))[0]


# ==============================================================================
# БЛОК 5: РЕРАНКИНГ (ПЕРЕСОРТИРОВКА НАЙДЕННЫХ ЧАНКОВ)
# ==============================================================================

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


# ==============================================================================
# БЛОК 6: ДОБАВЛЕНИЕ ДОКУМЕНТА В БАЗУ
# ==============================================================================

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


# ==============================================================================
# БЛОК 7: ГИБРИДНЫЙ ПОИСК (HYBRID SEARCH + RRF + RERANKER)
# ==============================================================================

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
    
    # 1. ВЕКТОРНЫЙ ПОИСК
    vector_stmt = (
        select(Document)
        .where(Document.embedding.cosine_distance(query_vector) < 0.5)
    )
    
    # Фильтр по тегам (JSONB ?| оператор)
    if tags:
        vector_stmt = vector_stmt.join(Upload, Document.upload_id == Upload.id).where(
            Upload.tags.op('?|')(cast(tags, ARRAY(String)))
        )
    
    vector_stmt = vector_stmt.order_by(Document.embedding.cosine_distance(query_vector)).limit(10)
    vector_docs = list((await session.execute(vector_stmt)).scalars().all())

    # 2. ТЕКСТОВЫЙ ПОИСК (BM25)
    text_stmt = (
        select(Document)
        .where(Document.tsv.op('@@')(func.plainto_tsquery('russian', query)))
    )
    
    if tags:
        text_stmt = text_stmt.join(Upload, Document.upload_id == Upload.id).where(
            Upload.tags.op('?|')(cast(tags, ARRAY(String)))
        )
        
    text_stmt = text_stmt.order_by(
        func.ts_rank_cd(Document.tsv, func.plainto_tsquery('russian', query)).desc()
    ).limit(10)
    text_docs = list((await session.execute(text_stmt)).scalars().all())

    # 3. RRF (объединение)
    rrf_scores = {}
    doc_map = {}

    for rank, doc in enumerate(vector_docs):
        doc_map[doc.id] = doc
        rrf_scores[doc.id] = rrf_scores.get(doc.id, 0) + 1.0 / (60 + rank + 1)

    for rank, doc in enumerate(text_docs):
        doc_map[doc.id] = doc
        rrf_scores[doc.id] = rrf_scores.get(doc.id, 0) + 1.0 / (60 + rank + 1)

    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    top_candidates = [doc_map[doc_id] for doc_id in sorted_ids[:10]]

    if not top_candidates:
        return []

    # 4. РЕРАНКИНГ
    return await rerank_documents(query, top_candidates, top_n=limit)


# ==============================================================================
# БЛОК 8: ФОРМАТИРОВАНИЕ КОНТЕКСТА ДЛЯ LLM
# ==============================================================================

def format_context(docs: list[Document]) -> str:
    if not docs:
        return ""
    parts = [f"[{d.source}]\n{d.text}" for d in docs]
    return "\n\n---\n\n".join(parts)