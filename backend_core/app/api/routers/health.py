from fastapi import APIRouter
from app.core.config import settings, APP_VERSION

router = APIRouter()

@router.get("/status")
async def get_status():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": APP_VERSION,
    }