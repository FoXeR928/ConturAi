from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models import Prompt

# ==============================================================================
# БЛОК 1: ДЕФОЛТНЫЕ ПРОМПТЫ (СИДЫ)
# ==============================================================================

# Источник правды для начальной инициализации базы данных.
# Вызывается через manage.py init-db.
DEFAULT_PROMPTS = {
    "ai_name": {
        "value": "Контур",
        "description": "Имя нейросети (подставляется в системный промт)",
    },
    "system_prompt": {
        "value": (
            "Ты — {name}, корпоративный ассистент.\n\n"
            "ПРАВИЛА ОТВЕТА:\n"
            "1. Отвечай на вопрос пользователя, используя ТОЛЬКО контекст ниже.\n"
            "2. Не копируй контекст целиком. Выдели только релевантные фрагменты.\n"
            "3. Если в контексте есть markdown-таблицы (строки с | и ---), "
            "сохраняй их формат в ответе. НЕ оборачивай таблицы в ``` или ```markdown.\n"
            "4. После каждого факта указывай источник в квадратных скобках: [имя_файла.md].\n"
            "5. Отвечай прямо на вопрос. Не пиши служебные фразы вроде «Вопрос пользователя:», "
            "«Ответ:» или «Контекст:».\n"
            "6. Если в контексте нет ответа — напиши: "
            "«В предоставленных документах этой информации нет».\n\n"
            "Контекст из базы знаний:\n"
            "{context}"
        ),
        "description": "Системный промт",
    },
    "user_prompt": {
        "value": "{quest}",
        "description": "Шаблон запроса. Доступен: {quest}",
    },
}


# ==============================================================================
# БЛОК 2: ЧТЕНИЕ ПРОМПТОВ (ДЛЯ АДМИНКИ И ЛОГИКИ LLM)
# ==============================================================================

async def list_prompts(session: AsyncSession) -> list[dict]:
    """
    Возвращает список промптов для отображения в админ-панели.
    Включает метаданные (описание, дата обновления), чтобы админ понимал, 
    какие промпты есть в системе и когда они менялись.
    """
    result = await session.execute(
        select(Prompt.key, Prompt.value, Prompt.description, Prompt.updated_at)
    )
    return [dict(r._mapping) for r in result.all()]


async def get_all_prompts(session: AsyncSession) -> dict[str, str]:
    """
    Возвращает промпты в виде простого словаря (ключ: значение).
    Используется внутри сервиса `ai_service.py` при сборке запроса к vLLM.
    Например: {"system_prompt": "Ты — {name}...", "ai_name": "Контур"}
    """
    result = await session.execute(select(Prompt.key, Prompt.value))
    return {k: v for k, v in result.all()}


# ==============================================================================
# БЛОК 3: ОБНОВЛЕНИЕ ПРОМПТА
# ==============================================================================

async def update_prompt(session: AsyncSession, key: str, value: str) -> None:
    """
    Обновляет текст конкретного промпта в базе данных.
    
    Проверяет, существует ли промпт с таким ключом. 
    Если нет — выбрасывает ошибку 404, чтобы админ не создавал "фантомные" записи.
    """
    # Проверка существования записи
    exists = (
        await session.execute(select(Prompt.id).where(Prompt.key == key))
    ).scalar_one_or_none()
    
    if not exists:
        raise AppError(f"Промт '{key}' не найден", "warning", 404)
        
    # Обновление значения
    await session.execute(update(Prompt).where(Prompt.key == key).values(value=value))
    await session.commit()