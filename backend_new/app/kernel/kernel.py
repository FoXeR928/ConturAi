from app.kernel.registry import Registry
from loguru import logger

class Kernel:
    def __init__(self):
        self.registry = Registry()
        self._current_plugin: str | None = None

    def begin_plugin(self, plugin_id: str):
        """Вызывается перед загрузкой плагина, чтобы связать все его регистрации с ним."""
        self._current_plugin = plugin_id

    def end_plugin(self):
        """Вызывается после загрузки плагина."""
        self._current_plugin = None

    # ---- Декораторы для плагинов ----

    def parser(self, cls):
        instance = cls()
        self.registry.parsers.append((self._current_plugin, instance))
        logger.info(f"  [{self._current_plugin}] + Parser: {cls.__name__}")
        return cls

    def router(self, prefix: str):
        def decorator(router_obj):
            self.registry.routers[self._current_plugin] = (prefix, router_obj)
            logger.info(f"  [{self._current_plugin}] + Router: {prefix}")
            return router_obj
        return decorator

    def hook(self, hook_name: str):
        def decorator(fn):
            self.registry.hooks[hook_name].append((self._current_plugin, fn))
            logger.info(f"  [{self._current_plugin}] + Hook: {hook_name}")
            return fn
        return decorator

    def rag_provider(self, cls):
        instance = cls()
        self.registry.rag_providers.append((self._current_plugin, instance))
        logger.info(f"  [{self._current_plugin}] + RAG Provider: {cls.__name__}")
        return cls

    def llm_provider(self, cls):
        """ДОБАВЛЕНО: Регистрация плагина как LLM-провайдера"""
        instance = cls()
        self.registry.llm_providers.append((self._current_plugin, instance))
        logger.info(f"  [{self._current_plugin}] + LLM Provider: {cls.__name__}")
        return cls

# Глобальный синглтон
kernel = Kernel()