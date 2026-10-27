from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.secrets import decode_token
from app.db.models import User
from app.db.session import get_session

# ==============================================================================
# БЛОК 1: НАСТРОЙКА СХЕМЫ АВТОРИЗАЦИИ (BEARER TOKEN)
# ==============================================================================

# Эта строка указывает FastAPI, что для авторизации используется JWT-токен 
# в заголовке `Authorization: Bearer <token>`.
# Параметр tokenUrl используется только для Swagger UI (/docs), чтобы там 
# появилась кнопка "Authorize" и форма ввода логина/пароля.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ==============================================================================
# БЛОК 2: БАЗОВАЯ ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ (АУТЕНТИФИКАЦИЯ)
# ==============================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Главная зависимость для проверки авторизации.
    
    Она делает следующее:
    1. Извлекает токен из заголовка запроса (через oauth2_scheme).
    2. Расшифровывает его (decode_token) и достает логин пользователя.
    3. Ищет этого пользователя в базе данных.
    4. Проверяет, что пользователь существует и не заблокирован (disabled=False).
    
    Если на любом этапе происходит ошибка, выбрасывается исключение 401 (Unauthorized).
    Если всё успешно — возвращает объект пользователя (User) из БД.
    """
    try:
        # Расшифровка JWT-токена. Если подпись неверна или токен истек — будет исключение.
        login = decode_token(token)
    except Exception as err:
        raise AppError("Неверный токен", "warning", 401) from err
        
    # Поиск пользователя в базе данных по логину из токена
    user = (
        await session.execute(select(User).where(User.login == login))
    ).scalar_one_or_none()
    
    # Защита: если пользователя удалили или заблокировали после выдачи токена
    if not user or user.disabled:
        raise AppError("Пользователь не найден", "warning", 401)
        
    return user


# ==============================================================================
# БЛОК 3: ПРОВЕРКА РОЛЕЙ (АВТОРИЗАЦИЯ / RBAC)
# ==============================================================================

async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """
    Зависимость для проверки прав администратора.
    
    Благодаря Depends(get_current_user) она сначала автоматически выполняет 
    всю проверку из Блока 2. То есть, если сюда дошел запрос, 
    значит пользователь уже гарантированно авторизован и активен.
    
    Далее проверяется флаг is_admin.
    Если это не админ — возвращается ошибка 403 (Forbidden).
    """
    if not user.is_admin:
        raise AppError("Доступно только администратору", "warning", 403)
    return user


async def get_editor_user(user: User = Depends(get_current_user)) -> User:
    """
    Зависимость для проверки прав редактора (или администратора).
    
    Редакторы имеют право загружать и удалять документы, но не имеют доступа 
    к управлению пользователями или системными настройками.
    В модели User свойство `is_editor` обычно проверяет, что роль равна 'editor' или 'admin'.
    """
    if not user.is_editor: # Предполагается, что свойство is_editor есть в модели User
        raise AppError("Требуется роль editor или admin", "warning", 403)
    return user