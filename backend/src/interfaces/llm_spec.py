"""
Контракты для подключаемых LLM-провайдеров и конвейера контекста.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterable, List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Универсальное сообщение, с которым работает пайплайн и провайдер."""
    role: str  # "system" | "user" | "assistant"
    content: str


class ContextMiddleware(ABC):
    """Один шаг обработки контекста (RAG, поиск, фильтрация, обрезка и т.д.)."""

    @abstractmethod
    async def process(
        self,
        messages: List[ChatMessage],
        *,
        room_id: Optional[str] = None,
    ) -> List[ChatMessage]:
        ...


class ContextPipeline:
    """Последовательность middleware-ов, выполняемая перед генерацией."""

    def __init__(self, middlewares: Optional[List[ContextMiddleware]] = None) -> None:
        self._middlewares: List[ContextMiddleware] = list(middlewares or [])

    def add(self, middleware: ContextMiddleware) -> "ContextPipeline":
        self._middlewares.append(middleware)
        return self

    async def run(
        self,
        messages: List[ChatMessage],
        *,
        room_id: Optional[str] = None,
    ) -> List[ChatMessage]:
        current = messages
        for mw in self._middlewares:
            current = await mw.process(current, room_id=room_id)
        return current


class InferenceProvider(ABC):
    """LLM-провайдер. Реализуется плагином (обычно remote).
    Ядро не знает, что за модель за этим интерфейсом."""

    #: Должен совпадать с id плагина — ядро берёт провайдера из активных.
    id: str = ""

    @abstractmethod
    async def stream(self, messages: List[ChatMessage]) -> AsyncIterable[str]:
        """Асинхронный стрим токенов ответа. messages — уже прошедшие
        ContextPipeline (ядро вызывает pipeline.run до stream())."""
        raise NotImplementedError
        yield ""  # pragma: no cover