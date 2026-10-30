"""
Базовые контракты для всех плагинов ConturAI.

Плагин — это директория в /plugins с файлом manifest.json и main.py.
main.py обязан экспортировать класс, наследующий NexusPlugin.

Плагины могут быть двух видов (по manifest["type"]):
  - "local"  — код исполняется в памяти ядра;
  - "remote" — ядро делегирует запуск Docker-контейнера ConturAi manager.

Опционально плагин может также реализовывать интерфейс InferenceProvider
(см. llm_spec.py) и/или возвращать ContextMiddleware из
get_context_middleware() — тогда его логика будет встроена в конвейер
подготовки контекста для активной LLM.
"""
from __future__ import annotations

from abc import ABC
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel


class NexusPlugin(ABC):
    """Базовый класс для любого плагина ConturAI."""

    #: Идентификатор (совпадает с manifest["id"], если не переопределён)
    id: str = ""
    #: Человекочитаемое имя
    name: str = ""
    #: Версия
    version: str = "0.1.0"

    # ---- Жизненный цикл --------------------------------------------------

    async def on_install(self) -> None:
        """Однократная установка (создание файлов, миграции, прогрев)."""
        return None

    async def on_activate(self, endpoint_url: Optional[str] = None) -> None:
        """Активация. Для remote-плагинов endpoint_url — внутренний URL
        контейнера (например, http://conturai-plugin-llm:8000)."""
        return None

    async def on_deactivate(self) -> None:
        """Деактивация. Плагин должен освободить ресурсы (закрыть клиентов)."""
        return None

    async def on_uninstall(self) -> None:
        """Полное удаление (вызывается при явном uninstall)."""
        return None

    # ---- Конфигурация ----------------------------------------------------

    def get_settings_blueprint(self) -> Optional[Type[BaseModel]]:
        """Возвращает Pydantic-модель настроек для динамической генерации
        формы на фронтенде. None — если настроек нет."""
        return None

    async def apply_settings(self, settings_data: Dict[str, Any]) -> None:
        """Применить сохранённые настройки. Вызывается после on_activate
        и при сохранении через admin API."""
        return None

    # ---- Участие в конвейере контекста ----------------------------------

    def get_context_middleware(self) -> Optional["ContextMiddleware"]:
        """Если плагин хочет модифицировать сообщения перед отправкой в LLM
        (например, RAG подмешивает найденные документы), он возвращает
        middleware. Ядро соберёт из них общий ContextPipeline."""
        return None