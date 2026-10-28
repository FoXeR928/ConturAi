from abc import ABC, abstractmethod

class BasePlugin(ABC):
    """Базовый класс для всех плагинов."""
    pass


class BaseParser(BasePlugin):
    """Плагин, умеющий извлекать текст из файлов."""
    
    @abstractmethod
    def can_handle(self, mime_type: str, filename: str) -> bool:
        """Может ли этот плагин обработать файл?"""
        pass

    @abstractmethod
    def parse(self, mime_type: str, data: bytes, filename: str = "") -> str:
        """Извлекает текст."""
        pass

class BaseRAGProvider(BasePlugin):
    """Интерфейс для плагинов поиска по документам (RAG)."""
    
    @abstractmethod
    async def add_document(self, session: Any, source: str, text: str, upload_id: Any = None) -> int:
        """Индексирует текст (нарезает на чанки и сохраняет вектора)."""
        pass

    @abstractmethod
    async def search(self, session: Any, query: str, tags: list[str] | None = None) -> list[Any]:
        """Ищет релевантные документы по запросу."""
        pass

    @abstractmethod
    def format_context(self, docs: list[Any]) -> str:
        """Склеивает найденные чанки в единый текст для промпта."""
        pass