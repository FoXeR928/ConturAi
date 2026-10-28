import uuid
from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text, ForeignKey, Index, DateTime, func, Computed
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models import Base # Импортируем Base из ядра
from app.core.config import settings

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(255), index=True)
    text: Mapped[str] = mapped_column(Text)
    text_norm: Mapped[str | None] = mapped_column(Text)
    page: Mapped[int] = mapped_column(default=1)
    
    # Ссылаемся на таблицу uploads ядра
    upload_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("uploads.id", ondelete="CASCADE"), index=True, nullable=True)
    
    language: Mapped[str] = mapped_column(String(8), default="ru")
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim))
    
    tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('russian', text)", persisted=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("documents_embedding_hnsw", "embedding", postgresql_using="hnsw", postgresql_with={"m": 16, "ef_construction": 64}, postgresql_ops={"embedding": "vector_cosine_ops"}),
        Index("documents_tsv_gin", "tsv", postgresql_using="gin"),
    )