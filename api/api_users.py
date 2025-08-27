from fastapi import APIRouter, Response, Depends
from pydantic import BaseModel

from api.api_auth import User, get_current_user
from db_modules.db_query_users import get_users

users_app = APIRouter(prefix="/users", tags=["Пользователи"])

@users_app.patch("/get", summary="Получение списка пользователей")
async def get_users_api(
    response: Response,current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = get_users()
    else:
        result = {
            "result": False,
            "message": "Доступно только администратору",
            "category": "warning",
            "cod": 403,
        }
    response.status_code = result["cod"]
    del result["cod"]
    return result