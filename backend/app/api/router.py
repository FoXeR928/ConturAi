from fastapi import APIRouter

from app.api.v1 import ai, auth, chats, prompts, users, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(chats.router, prefix="/chats", tags=["Chats"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])