import asyncio
import re
from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymorphy3 import MorphAnalyzer
from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Document, Upload
from app.services import llm_config_service

# ==============================================================================
# БЛОК 1: НОРМАЛИЗАЦИЯ ТЕКСТА (ДЛЯ ПОИСКА)
# ==============================================================================

# Инициализируем морфологический анализатор для русского языка.
# Он нужен для приведения слов к начальной форме (лемме), 
# чтобы поиск находил "документ" по запросу "документы".
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
    
    - chunk_size: размер чанка в символах.
    - chunk_overlap: перекрытие. Нужно, чтобы не разрывать смысл предложений на границе чанков.
    Использует умные разделители: сначала пытается резать по абзацам, потом по предложениям.
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

# lru_cache(maxsize=1) гарантирует, что модель загрузится в оперативную память (RAM) 
# только один раз при первом запросе, и будет переиспользоваться дальше.
# device="cpu" указан намеренно, чтобы не занимать VRAM видеокарты, 
# которая нужна для vLLM (генерации текста).

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
    """
    Генерирует вектора для списка текстов.
    Обязательно выносим синхронную работу модели в отдельный поток (run_in_executor),
    чтобы не блокировать Event Loop FastAPI (иначе сервер зависнет на время расчета).
    """
    loop = asyncio.get_running_loop()
    model = get_model()

    def _encode() -> list[list[float]]:
        # normalize_embeddings=True обеспечивает косинусное расстояние
        vectors = model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vectors]

    return await loop.run_in_executor(None, _encode)

async def embed_one(text: str) -> list[float]:
    """Обертка для получения вектора одного запроса пользователя."""
    return (await embed_texts([text]))[0]


# ==============================================================================
# БЛОК 5: РЕРАНКИНГ (ПЕРЕСОРТИРОВКА НАЙДЕННЫХ ЧАНКОВ)
# ==============================================================================

async def rerank_documents(query: str, docs: list[Document], top_n: int) -> list[Document]:
    """
    Cross-Encoder — это более тяжелая и точная модель, чем обычный эмбеддер.
    Она берет пару (Запрос + Чанк) и выдает оценку релевантности от 0 до 1.
    Используется для финальной сортировки топ-10 документов.
    """
    if not docs:
        return []
    
    loop = asyncio.get_running_loop()
    model = get_reranker()
    pairs = [[query, doc.text] for doc in docs]
    
    def _predict():
        return model.predict(pairs)

    scores = await loop.run_in_executor(None, _predict)
    
    # Объединяем документы с их оценками и сортируем по убыванию
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
    """
    Нарезает документ на чанки, генерирует для них вектора и сохраняет в PostgreSQL.
    Возвращает количество созданных чанков.
    """
    cfg = await llm_config_service.get_rag(session)
    chunks = split_text(text, cfg["chunk_size"], cfg["chunk_overlap"])
    if not chunks:
        return 0

    points: list[Document] = []
    
    # Обрабатываем батчами (по 64 штуки), чтобы не перегружать память
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
    """
    Самый важный метод RAG. Ищет релевантные чанки по базе.
    Использует современный подход (Hybrid Search).
    """
    if limit is None:
        cfg = await llm_config_service.get_rag(session)
        limit = cfg["search_limit"]

    query_vector = await embed_one(query)
    
    # --- ШАГ 1: ВЕКТОРНЫЙ ПОИСК (Семантический) ---
    # Ищет по смыслу. Даже если слова разные, но смысл близок, он найдет.
    vector_stmt = (
        select(Document)
        .where(Document.embedding.cosine_distance(query_vector) < 0.5)
    )
    if tags:
        vector_stmt = vector_stmt.join(Upload, Document.upload_id == Upload.id).where(Upload.tags.overlap(tags))
    
    vector_stmt = vector_stmt.order_by(Document.embedding.cosine_distance(query_vector)).limit(10)
    vector_docs = list((await session.execute(vector_stmt)).scalars().all())

    # --- ШАГ 2: ПОЛНОТЕКСТОВЫЙ ПОИСК (Точные слова) ---
    # Ищет по ключевым словам (BM25/ts_rank). Важно для поиска артикулов, имен и аббревиатур,
    # которые векторный поиск может упустить.
    text_stmt = (
        select(Document)
        .where(Document.tsv.op('@@')(func.plainto_tsquery('russian', query)))
    )
    if tags:
        text_stmt = text_stmt.join(Upload, Document.upload_id == Upload.id).where(Upload.tags.overlap(tags))
        
    text_stmt = text_stmt.order_by(
        func.ts_rank_cd(Document.tsv, func.plainto_tsquery('russian', query)).desc()
    ).limit(10)
    text_docs = list((await session.execute(text_stmt)).scalars().all())

    # --- ШАГ 3: RRF (Reciprocal Rank Fusion) ---
    # Объединяем результаты двух поисков в один список. 
    # Формула: Score = 1 / (60 + rank). Чем выше документ в обоих списках, тем больше его итоговый скор.
    rrf_scores = {}
    doc_map = {}

    for rank, doc in enumerate(vector_docs):
        doc_map[doc.id] = doc
        rrf_scores[doc.id] = rrf_scores.get(doc.id, 0) + 1.0 / (60 + rank + 1)

    for rank, doc in enumerate(text_docs):
        doc_map[doc.id] = doc
        rrf_scores[doc.id] = rrf_scores.get(doc.id, 0) + 1.0 / (60 + rank + 1)

    # Сортируем по объединенному скору и берем топ-10 для реранкера
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    top_candidates = [doc_map[doc_id] for doc_id in sorted_ids[:10]]

    if not top_candidates:
        return []

    # --- ШАГ 4: РЕРАНКИНГ ---
    # Финальная пересортировка топ-10 кандидатов с помощью тяжелой Cross-Encoder модели.
    return await rerank_documents(query, top_candidates, top_n=limit)


# ==============================================================================
# БЛОК 8: ФОРМАТИРОВАНИЕ КОНТЕКСТА ДЛЯ LLM
# ==============================================================================

def format_context(docs: list[Document]) -> str:
    """
    Склеивает найденные чанки в единый текст для промпта.
    Каждый чанк оборачивается в [имя_файла], чтобы LLM знала, 
    откуда взята информация, и могла ссылаться на источник.
    """
    if not docs:
        return ""
    parts = [f"[{d.source}]\n{d.text}" for d in docs]
    return "\n\n---\n\n".join(parts)