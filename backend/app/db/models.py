import uuid
from datetime import datetime

import bcrypt
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    Computed,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    login: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    user_name: Mapped[str | None] = mapped_column(String(128))
    
    # --- RBAC ---
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    chat_role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    @property
    def is_editor(self) -> bool:
        return self.role in ("admin", "editor")

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return (
            bcrypt.checkpw(password.encode(), self.password_hash.encode())
            and not self.disabled
        )


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_login: Mapped[str] = mapped_column(
        ForeignKey("users.login", ondelete="CASCADE", onupdate="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_login: Mapped[str] = mapped_column(
        ForeignKey("users.login", ondelete="CASCADE", onupdate="CASCADE"), index=True
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(255), index=True)
    text: Mapped[str] = mapped_column(Text)
    text_norm: Mapped[str | None] = mapped_column(Text)
    page: Mapped[int] = mapped_column(default=1)
    upload_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("uploads.id", ondelete="CASCADE"), index=True, nullable=True
    )
    language: Mapped[str] = mapped_column(String(8), default="ru")
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim))
    
    # --- Гибридный поиск ---
    tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, 
        Computed("to_tsvector('russian', text)", persisted=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index(
            "documents_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "documents_tsv_gin",
            "tsv",
            postgresql_using="gin",
        ),
    )


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(String(255))
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )


class LlmConfig(Base):
    __tablename__ = "llm_configs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(String(255))
    input_type: Mapped[str] = mapped_column(String(32), default="text")
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # <-- Шифрование
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    original_name: Mapped[str] = mapped_column(String(255), index=True)
    stored_name: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size: Mapped[int] = mapped_column(default=0)
    text: Mapped[str] = mapped_column(Text)
    uploaded_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.login", ondelete="SET NULL", onupdate="CASCADE"),
        index=True,
        nullable=True,
    )
    chunks_count: Mapped[int] = mapped_column(default=0)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, default=list, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DownloadRequest(Base):
    __tablename__ = "download_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_login: Mapped[str] = mapped_column(ForeignKey("users.login", ondelete="CASCADE"), index=True)
    upload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("uploads.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending") # pending, approved, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_login: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    details: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FewShot(Base):
    __tablename__ = "few_shots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )