from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Document
from app.rag.chunker import normalize_text, split_text
from app.rag.embeddings import embed_texts, embed_one


async def add_document(
    session: AsyncSession, source: str, text: str
) -> int:
    chunks = split_text(text)
    if not chunks:
        return 0

    norm_full = normalize_text(text)

    points: list[Document] = []
    batch_size = settings.rag_batch_size
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vectors = await embed_texts(batch)
        for j, (chunk, vector) in enumerate(zip(batch, vectors)):
            points.append(
                Document(
                    source=source,
                    text=chunk,
                    text_norm=norm_full,
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