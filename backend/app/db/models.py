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

# ==============================================================================
# БЛОК 1: БАЗОВЫЙ КЛАСС ДЛЯ ВСЕХ МОДЕЛЕЙ
# ==============================================================================

class Base(DeclarativeBase):
    """
    Базовый класс, от которого наследуются все таблицы.
    Автоматически регистрирует модели в метаданных SQLAlchemy.
    """
    pass


# ==============================================================================
# БЛОК 2: ПОЛЬЗОВАТЕЛИ И РОЛИ
# ==============================================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    login: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255)) # Bcrypt-хэш
    user_name: Mapped[str | None] = mapped_column(String(128))     # Отображаемое имя
    
    # Роль пользователя: admin (полный доступ), editor (работа с документами) или user.
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    
    # is_system = True только для служебного аккаунта "system" (от его имени ИИ пишет ответы).
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Роль в чате (user / assistant). Нужна для формирования истории промптов для LLM.
    chat_role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    
    disabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    @property
    def is_admin(self) -> bool:
        """Удобное свойство для проверки прав администратора."""
        return self.role == "admin"

    @property
    def is_editor(self) -> bool:
        """Проверка, может ли пользователь загружать/удалять документы."""
        return self.role in ("admin", "editor")

    def set_password(self, password: str) -> None:
        """Хэширует пароль с помощью bcrypt перед сохранением в БД."""
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password: str) -> bool:
        """Проверяет пароль. Возвращает False, если пользователь заблокирован."""
        if not self.password_hash:
            return False
        return (
            bcrypt.checkpw(password.encode(), self.password_hash.encode())
            and not self.disabled
        )


# ==============================================================================
# БЛОК 3: ЧАТЫ И СООБЩЕНИЯ
# ==============================================================================

class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_login: Mapped[str] = mapped_column(ForeignKey("users.login", ondelete="CASCADE", onupdate="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    
    # Мягкое удаление: чат не стирается, а перемещается в корзину.
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # При удалении пользователя удалятся и его сообщения (CASCADE)
    user_login: Mapped[str] = mapped_column(ForeignKey("users.login", ondelete="CASCADE", onupdate="CASCADE"), index=True)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # --- Метрики для статистики LLM ---
    prompt_tokens: Mapped[int] = mapped_column(default=0)       # Токенов во входном промпте
    completion_tokens: Mapped[int] = mapped_column(default=0)   # Токенов в ответе модели
    duration_ms: Mapped[int] = mapped_column(default=0)         # Время генерации в миллисекундах


# ==============================================================================
# БЛОК 4: ДОКУМЕНТЫ ДЛЯ RAG (ВЕКТОРНАЯ БАЗА)
# ==============================================================================

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(255), index=True) # Имя файла (для цитирования)
    text: Mapped[str] = mapped_column(Text)                      # Текст чанка
    text_norm: Mapped[str | None] = mapped_column(Text)          # Лемматизированный текст (для поиска)
    page: Mapped[int] = mapped_column(default=1)                 # Номер страницы (или порядковый номер чанка)
    
    # Привязка к загруженному файлу (если чанк извлечен из файла)
    upload_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("uploads.id", ondelete="CASCADE"), index=True, nullable=True)
    
    language: Mapped[str] = mapped_column(String(8), default="ru")
    
    # Векторное представление текста (размерность 1024 для e5-large).
    # Хранится в специальном типе pgvector.
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim))
    
    # --- Гибридный поиск (Full-Text Search) ---
    # Колонка автоматически обновляется PostgreSQL при изменении поля text.
    # Используется для поиска по ключевым словам (в дополнение к векторному поиску).
    tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, 
        Computed("to_tsvector('russian', text)", persisted=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # Индекс HNSW для быстрого семантического поиска по векторам.
        # cosine_ops используется, так как эмбеддинги нормализованы (косинусное расстояние).
        Index(
            "documents_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        # GIN-индекс для быстрого полнотекстового поиска.
        Index(
            "documents_tsv_gin",
            "tsv",
            postgresql_using="gin",
        ),
    )


# ==============================================================================
# БЛОК 5: СПРАВОЧНИКИ И НАСТРОЙКИ
# ==============================================================================

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    color: Mapped[str] = mapped_column(String(7), default="#3b82f6") # HEX-цвет для UI
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True) # ai_name, system_prompt и т.д.
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(String(255))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class LlmConfig(Base):
    __tablename__ = "llm_configs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True) # vllm_temperature и т.д.
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(String(255))
    input_type: Mapped[str] = mapped_column(String(32), default="text")   # text, number, boolean
    
    # Если True, значение шифруется перед сохранением (используется для API-ключей)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) 
    
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())


# ==============================================================================
# БЛОК 6: ФАЙЛЫ И УПРАВЛЕНИЕ ДОСТУПОМ
# ==============================================================================

class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    original_name: Mapped[str] = mapped_column(String(255), index=True)
    stored_name: Mapped[str | None] = mapped_column(String(255)) # Имя файла на диске (uuid.pdf)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size: Mapped[int] = mapped_column(default=0)
    text: Mapped[str] = mapped_column(Text)                      # Извлеченный из файла текст
    
    # Кто загрузил файл. Если пользователя удалят, поле станет NULL.
    uploaded_by: Mapped[str | None] = mapped_column(ForeignKey("users.login", ondelete="SET NULL", onupdate="CASCADE"), index=True, nullable=True)
    
    chunks_count: Mapped[int] = mapped_column(default=0)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, default=list, nullable=True) # Массив тегов
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DownloadRequest(Base):
    __tablename__ = "download_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_login: Mapped[str] = mapped_column(ForeignKey("users.login", ondelete="CASCADE"), index=True)
    
    upload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("uploads.id", ondelete="CASCADE"), index=True)
    chat_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=True)

    # Статус заявки: pending (ожидает), approved (одобрено), rejected (отклонено)
    status: Mapped[str] = mapped_column(String(32), default="pending") 
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)) # Срок действия разрешения


# ==============================================================================
# БЛОК 7: БЕЗОПАСНОСТЬ И ОБУЧЕНИЕ (FEW-SHOT)
# ==============================================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_login: Mapped[str] = mapped_column(String(64), index=True)  # Кто сделал
    action: Mapped[str] = mapped_column(String(128), index=True)     # Что сделал (upload_doc, login и т.д.)
    details: Mapped[str | None] = mapped_column(Text)                # Подробности
    ip_address: Mapped[str | None] = mapped_column(String(45))       # IP-адрес (до 45 символов для IPv6)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FewShot(Base):
    __tablename__ = "few_shots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())