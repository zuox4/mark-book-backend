import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database.database import get_db
from app.services.registration_service import RegistrationService
from app.database.models import User

from app.auth.utils import create_access_token
from app.core.config import settings
from app.auth.dependencies import get_current_active_user, get_current_user
from app.auth.models import RegisterRequest, VerifyEmailRequest, LoginRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter()

@router.get("/{id}", response_model=dict)
async def get_user_main_data(current_user: User = Depends(get_current_active_user),  db: Session = Depends(get_db)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        }


