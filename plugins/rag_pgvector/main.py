import httpx
from sqlalchemy import select, func, cast, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from app.kernel import kernel
from app.kernel.contracts import BaseRAGProvider
from app.services import llm_config_service
from app.db.models import Upload
from .models import Document
from .utils import split_text, normalize_text # (Функции нарезки оставляем локально)

EMBEDDER_URL = "http://rag_embedder_service:8080"

@kernel.rag_provider
class PgVectorRAG(BaseRAGProvider):
    
    async def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Обращается к Sidecar-сервису за векторами."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(f"{EMBEDDER_URL}/embed", json={"texts": texts})
            res.raise_for_status()
            return res.json()["vectors"]

    async def add_document(self, session: AsyncSession, source: str, text: str, upload_id=None) -> int:
        cfg = await llm_config_service.get_rag(session)
        chunks = split_text(text, cfg["chunk_size"], cfg["chunk_overlap"])
        if not chunks:
            return 0

        points = []
        for i in range(0, len(chunks), cfg["batch_size"]):
            batch = chunks[i : i + cfg["batch_size"]]
            vectors = await self._get_embeddings(batch) # <-- HTTP Запрос
            for j, (chunk, vector) in enumerate(zip(batch, vectors)):
                points.append(
                    Document(
                        source=source, text=chunk, text_norm=normalize_text(chunk),
                        page=i + j + 1, language="ru", embedding=vector, upload_id=upload_id,
                    )
                )
        session.add_all(points)
        await session.commit()
        return len(points)

    async def search(self, session: AsyncSession, query: str, tags: list[str] | None = None) -> list[Document]:
        cfg = await llm_config_service.get_rag(session)
        limit = cfg["search_limit"]

        # 1. Получаем вектор запроса
        query_vectors = await self._get_embeddings([query])
        query_vector = query_vectors[0]

        # 2. Векторный поиск в БД (без изменений)
        vector_stmt = select(Document).where(Document.embedding.cosine_distance(query_vector) < 0.5)
        if tags:
            vector_stmt = vector_stmt.join(Upload, Document.upload_id == Upload.id).where(
                Upload.tags.op('?|')(cast(tags, ARRAY(String)))
            )
        vector_stmt = vector_stmt.order_by(Document.embedding.cosine_distance(query_vector)).limit(10)
        vector_docs = list((await session.execute(vector_stmt)).scalars().all())

        # 3. Текстовый поиск в БД (без изменений)
        text_stmt = select(Document).where(Document.tsv.op('@@')(func.plainto_tsquery('russian', query)))
        if tags:
            text_stmt = text_stmt.join(Upload, Document.upload_id == Upload.id).where(
                Upload.tags.op('?|')(cast(tags, ARRAY(String)))
            )
        text_stmt = text_stmt.order_by(
            func.ts_rank_cd(Document.tsv, func.plainto_tsquery('russian', query)).desc()
        ).limit(10)
        text_docs = list((await session.execute(text_stmt)).scalars().all())

        # 4. RRF
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

        # 5. РЕРАНКИНГ (через HTTP)
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                f"{EMBEDDER_URL}/rerank",
                json={"query": query, "documents": [d.text for d in top_candidates]}
            )
            res.raise_for_status()
            scores = res.json()["scores"]

        # Сортируем по скору и возвращаем топ
        scored_docs = list(zip(top_candidates, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored_docs[:limit]]

    def format_context(self, docs: list[Document]) -> str:
        if not docs: return ""
        return "\n\n---\n\n".join([f"[{d.source}]\n{d.text}" for d in docs])