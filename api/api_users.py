from fastapi import APIRouter, Response, Depends
from pydantic import BaseModel

from api.api_auth import User, get_current_user
from db_modules.db_query_users import get_users_query,registration_user_query

users_app = APIRouter(prefix="/users", tags=["Пользователи"])

class RegistrationUser(BaseModel):
    login: str
    user_name: str
    password:str

@users_app.get("/get", summary="Получение списка пользователей")
async def get_users_api(
    response: Response,current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = get_users_query()
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

@users_app.post("/registration", summary="Создание пользователя")
async def registration_users_api(
    response: Response,registration_user:RegistrationUser,current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = registration_user_query(login=registration_user.login,user_name=registration_user.user_name,password=registration_user.password)
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