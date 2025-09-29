from fastapi import APIRouter

from .admin import router as admin_router
from .auth import router as auth_router
"""Тут регистрируем все роутеры с префиксами"""

api_router = APIRouter()

api_router.include_router(admin_router, prefix="/users", tags=["users"])
api_router.include_router(auth_router, prefix="/auth", tags=["authentification"])

@api_router.get("/health", tags=["health"])
def api_health_check():

    return {"status": "healthy", "message": "API is running"}
