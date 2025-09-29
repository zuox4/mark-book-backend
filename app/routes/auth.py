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

@router.post("/register", response_model=dict)
async def register(
        register_data: RegisterRequest,
        db: Session = Depends(get_db)
):
    """Регистрация нового пользователя с отправкой email подтверждения"""
    try:
        user = RegistrationService.register_user(
            db=db,

            email=register_data.email,
            password=register_data.password,
            user_data=register_data.user_data
        )

        return {
            "message": "Registration successful. Please check your email to verify your account.",
            "user_id": user.id,
            "email": user.email,
            "note": "Account will be activated after email verification"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-email", response_model=dict)
async def verify_email(
        verify_data: VerifyEmailRequest,
        db: Session = Depends(get_db)
):
    """Подтверждение email адреса"""
    try:
        user = RegistrationService.verify_email(db, verify_data.token)

        # Создаем токен для автоматического входа
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires
        )

        return {
            "message": "Email verified successfully! Your account is now active.",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "external_id": user.external_id,
                "email": user.email,
                "display_name": user.display_name,
                "is_verified": user.is_verified
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# @router.post("/resend-verification", response_model=dict)
# async def resend_verification(
#         resend_data: ResendVerificationRequest,
#         db: Session = Depends(get_db)
# ):
#     """Повторная отправка email подтверждения"""
#     try:
#         success = RegistrationService.resend_verification_email(db, resend_data.email)
#
#         if success:
#             return {
#                 "message": "Verification email sent successfully. Please check your inbox."
#             }
#         else:
#             raise HTTPException(
#                 status_code=500,
#                 detail="Failed to send verification email. Please try again later."
#             )
#
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=dict)
async def login(
        login_data: LoginRequest,
        db: Session = Depends(get_db)
):
    """Вход в систему"""
    user = UserService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Проверяем подтвержден ли email
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please check your email for verification link."
        )

    # Проверяем активен ли аккаунт
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is not active. Please contact administrator."
        )

    # Обновляем время последнего входа
    user.last_login_at = datetime.datetime.utcnow()
    db.commit()



    # Создаем токен
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "external_id": user.external_id,
            "email": user.email,
            "is_verified": user.is_verified,
            "display_name": user.display_name,
            "roles": [i.name for i in user.roles],
        },
        "message": "Login successful"
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user(
        current_user: User = Depends(get_current_active_user)
):
    """Получить информацию о текущем пользователе"""

    return current_user


