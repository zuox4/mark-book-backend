import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database.database import get_db
from app.services.registration_service import RegistrationService
from app.database.models import User

from app.auth.utils import create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.auth.dependencies import get_current_active_user, get_current_user
from app.auth.models import RegisterRequest, VerifyEmailRequest, LoginRequest, UserResponse, RefreshTokenRequest
from app.services.user_service import UserService

router = APIRouter()

@router.post("/register", response_model=dict)
def register(
        register_data: RegisterRequest,
        db: Session = Depends(get_db)
):
    """Регистрация нового пользователя с отправкой email подтверждения"""
    try:
        user = RegistrationService.register_user(
            db=db,
            email=register_data.email,
            password=register_data.password,

        )

        return {
            "message": "Регистрация прошла успешно. Пожалуйста проверьте почтовый ящик",
            "user_id": user.id,
            "email": user.email,
            "note": "Аккаунт будет активирован после верификации"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-email", response_model=dict)
def verify_email(
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
            "message": "Email успешно верифицирован!",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "external_id": user.external_id,
                "email": user.email,
                "display_name": user.display_name,
                "is_verified": user.is_verified,
                "roles": [i.name for i in user.roles],
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
def login(
        login_data: LoginRequest,
        db: Session = Depends(get_db)
):
    """Вход в систему"""

    user = UserService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверные логин или пароль!")
    # Проверяем пройдена ли регистрация пользователем
    if user.requires_password:
        raise HTTPException(status_code=401, detail="Необходимо пройти регистрацию")
    # Проверяем подтвержден ли email
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email не подтвержден. Пожалуйста проверьте эл.почту"
        )
    # Проверяем активен ли аккаунт
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Аккаунт отключен. Пожалуйста свяжитесь с администратором"
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
    # Создаем refresh token (с большим сроком жизни)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id, "type": "refresh"},
        expires_delta=refresh_token_expires
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
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
def get_current_user(
        current_user: User = Depends(get_current_active_user)
):
    print(current_user.roles)
    """Получить информацию о текущем пользователе"""
    res = {
        "email": current_user.email,
        "display_name": current_user.display_name,
        "roles": [i.name for i in current_user.roles],
    }
    return res


@router.post("/refresh", response_model=dict)
def refresh_token(
        refresh_data: RefreshTokenRequest,
        db: Session = Depends(get_db)
):
    """Обновление access token с помощью refresh token"""
    try:
        # Проверяем refresh token
        payload = verify_token(refresh_data.refresh_token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Невалидный токен")

        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if email is None or user_id is None:
            raise HTTPException(status_code=401, detail="Невалидный токен")

        # Получаем пользователя из базы
        user = db.query(User).filter(User.id == user_id, User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")

        # Проверяем активность пользователя
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Аккаунт отключен")

        # Создаем новый access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires
        )
        # Создаем новый refresh token (опционально - можно ротировать)
        new_refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id, "type": "refresh"},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,  # Добавьте это
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "external_id": user.external_id,
                "email": user.email,
                "is_verified": user.is_verified,
                "display_name": user.display_name,
                "roles": [i.name for i in user.roles],
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при обновлении токена")