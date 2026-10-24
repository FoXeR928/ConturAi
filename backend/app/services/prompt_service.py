from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models import Prompt

# Дефолтные промты, которые будут добавлены при инициализации БД
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


async def list_prompts(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(Prompt.key, Prompt.value, Prompt.description, Prompt.updated_at)
    )
    return [dict(r._mapping) for r in result.all()]


async def get_all_prompts(session: AsyncSession) -> dict[str, str]:
    result = await session.execute(select(Prompt.key, Prompt.value))
    return {k: v for k, v in result.all()}


async def update_prompt(session: AsyncSession, key: str, value: str) -> None:
    exists = (
        await session.execute(select(Prompt.id).where(Prompt.key == key))
    ).scalar_one_or_none()
    if not exists:
        raise AppError(f"Промт '{key}' не найден", "warning", 404)
    await session.execute(update(Prompt).where(Prompt.key == key).values(value=value))
    await session.commit()