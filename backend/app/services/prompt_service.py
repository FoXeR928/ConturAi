from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models import Prompt

# Дефолтные промты, которые будут добавлены при инициализации БД
DEFAULT_PROMPTS = {
    "ai_name": {
        "value": "Раги",
        "description": "Имя нейросети (подставляется в системный промт)",
    },
    "system_prompt": {
        "value": (
            "Ты - {name}. Отвечай на вопросы, используя контекст из базы. "
            "Если данных нет — отвечай самостоятельно и добавляй "
            "'Ответ сгенерирован самостоятельно'"
        ),
        "description": "Системный промт. Доступны {name}",
    },
    "user_prompt": {
        "value": "Контекст: {context}\nВопрос: {quest}",
        "description": "Шаблон запроса. Доступны {context}, {quest}",
    },
}


async def list_prompts(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(Prompt.key, Prompt.value, Prompt.description, Prompt.updated_at)
    )
    return [dict(r._mapping) for r in result.all()]


async def get_prompt(session: AsyncSession, key: str) -> str | None:
    return (
        await session.execute(select(Prompt.value).where(Prompt.key == key))
    ).scalar_one_or_none()


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