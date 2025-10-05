import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database.database import get_db
from app.services import SchoolService
from app.services.registration_service import RegistrationService
from app.database.models import User

from app.auth.utils import create_access_token
from app.core.config import settings
from app.auth.dependencies import get_current_active_user, get_current_user
from app.auth.models import RegisterRequest, VerifyEmailRequest, LoginRequest, UserResponse


router = APIRouter()

@router.get("/{id}", response_model=dict)
async def get_user_main_data(current_user: User = Depends(get_current_active_user),  db: Session = Depends(get_db)):
    print(current_user.display_name)
    roles = [i.name for i in current_user.roles]
    print(current_user.image)

    return {
        "id": current_user.id,
        "display_name": current_user.display_name,
        "email": current_user.email,
        "image": current_user.image,
        "roles": roles,
        }


@router.get("/{id}", response_model=dict)
async def get_project_office_info(current_user: User = Depends(get_current_active_user),  db: Session = Depends(get_db)):
    print(current_user.display_name)
    roles = [i.name for i in current_user.roles]
    print(current_user.image)

    return {
        "id": current_user.id,
        "display_name": current_user.display_name,
        "email": current_user.email,
        "image": current_user.image,
        "roles": roles,
        }