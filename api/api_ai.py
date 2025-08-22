from fastapi import APIRouter, Response
from pydantic import BaseModel

from db_modules.db_query import admin_auth_check, user_auth_check, check_user
from db_modules.db_query_ai import r

ai_app = APIRouter(prefix="/AI", tags=["Нейросеть"])
