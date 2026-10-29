from collections import defaultdict
from typing import Any
from loguru import logger
from app.kernel.contracts import BaseParser, BaseLLMProvider

class Registry:
    def __init__(self):
        # Храним кортежи (plugin_id, instance), чтобы можно было удалять по плагину
        self.parsers: list[tuple[str, BaseParser]] = []
        self.routers: dict[str, tuple[str, Any]] = {}
        self.hooks: dict[str, list[tuple[str, Any]]] = defaultdict(list)
        self.rag_providers: list[tuple[str, Any]] = []
        self.llm_providers: list[tuple[str, BaseLLMProvider]] = []  # <-- ДОБАВЛЕНО

    # =========================================================================
    # Геттеры для сервисов
    # =========================================================================

    def get_parser(self, mime_type: str, filename: str) -> BaseParser | None:
        for _, parser in self.parsers:
            if parser.can_handle(mime_type, filename):
                return parser
        return None

    def get_rag_provider(self) -> Any | None:
        if self.rag_providers:
            return self.rag_providers[0][1] # Берем первый активный
        return None

    def get_llm_provider(self) -> BaseLLMProvider | None:
        """ДОБАВЛЕНО: Возвращает активный LLM-плагин"""
        if self.llm_providers:
            return self.llm_providers[0][1]
        return None

    # =========================================================================
    # Очистка
    # =========================================================================

    def clear_plugin(self, plugin_id: str):
        """Удаляет всё, что зарегистрировал конкретный плагин."""
        self.parsers = [(pid, p) for pid, p in self.parsers if pid != plugin_id]
        self.rag_providers = [(pid, p) for pid, p in self.rag_providers if pid != plugin_id]
        self.llm_providers = [(pid, p) for pid, p in self.llm_providers if pid != plugin_id]  # <-- ДОБАВЛЕНО
        self.routers.pop(plugin_id, None)
        for hook_name in list(self.hooks.keys()):
            self.hooks[hook_name] = [
                (pid, fn) for pid, fn in self.hooks[hook_name] if pid != plugin_id
            ]
        logger.info(f"[Registry] Очищен плагин '{plugin_id}'")