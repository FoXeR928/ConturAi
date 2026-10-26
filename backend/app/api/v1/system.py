from fastapi import APIRouter, Depends
from app.api.deps import get_admin_user
from app.db.models import User
from app.services import system_service

router = APIRouter()

@router.get("/stats")
async def get_stats(_: User = Depends(get_admin_user)):
    return {
        "result": True,
        "stats": system_service.get_system_stats(),
        "message": "Метрики получены",
        "category": "success"
    }