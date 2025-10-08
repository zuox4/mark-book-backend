from fastapi import APIRouter

from .admin import router as admin_router
from .auth import router as auth_router
from .user import router as user_router
from .student import router as student_router
from .event_types import router as event_type_router
"""Тут регистрируем все роутеры с префиксами"""

api_router = APIRouter()

api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(auth_router, prefix="/auth", tags=["authentification"])
api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(student_router, prefix="/student", tags=["student"])
api_router.include_router(event_type_router, prefix="/event-types", tags=["event-types"])
@api_router.get("/health", tags=["health"])
def api_health_check():

    return {"status": "healthy", "message": "API is running"}
