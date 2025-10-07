from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models.users import User
from app.database.models.roles import Role
from app.auth.utils import get_password_hash, verify_password
from app.services.resend_email_service import ResendEmailService
from app.services.SchoolServices import SchoolService
class RegistrationService:

    @staticmethod
    def register_user(
            db: Session,
            email: str,
            password: str,
    ) -> User:
        """Регистрация нового пользователя с отправкой email подтверждения"""
        # Проверяем не существует ли пользователь
        existing_user = db.query(User).filter(
            (User.email == email)
        ).first()


        if existing_user and not existing_user.requires_password:
            raise ValueError("Пользователь с таким email уже существует")
        if not existing_user:
            raise ValueError("Пользователь с таким email не найден в базе данных школы")


        # Генерируем токен верификации
        verification_token = ResendEmailService.generate_verification_token()

        existing_user.password_hash=get_password_hash(password),
        existing_user.verification_token=verification_token,
        existing_user.verification_sent_at=datetime.utcnow(),
        db.commit()
        db.refresh(existing_user)

        # Отправляем email подтверждения
        email_sent = ResendEmailService.send_verification_email(
            db=db,
            email=email,
            verification_token=verification_token,
            user_name=existing_user.display_name
        )

        if not email_sent:
            print(f"⚠️ Не удалось отправить email подтверждения для {email}")
        else:
            print(f"📧 Email подтверждения отправлен на: {email}")

        return existing_user

    @staticmethod
    def verify_email(db: Session, verification_token: str) -> User:
        """Подтверждение email по токену"""
        user = db.query(User).filter(
            User.verification_token == verification_token,
            User.is_verified == False
        ).first()

        if not user:
            raise ValueError("Неверный или устаревший токен подтверждения")

        # Проверяем не истек ли токен (24 часа)
        token_expiration = user.verification_sent_at + timedelta(hours=24)
        if datetime.utcnow() > token_expiration:
            raise ValueError("Срок действия токена подтверждения истек")

        # Активируем пользователя
        user.is_active = True
        user.is_verified = True
        user.requires_password = False
        user.email_verified_at = datetime.utcnow()
        user.verification_token = None  # Удаляем использованный токен
        db.commit()
        db.refresh(user)

        ResendEmailService.send_welcome_email(
            email=user.email,
            user_name=user.display_name
        )

        print(f"✅ Email подтвержден для: {user.email}")
        return user

    @staticmethod
    def resend_verification_email(db: Session, email: str) -> bool:
        """Повторная отправка email подтверждения"""
        user = db.query(User).filter(
            User.email == email,
            User.is_verified == False
        ).first()

        if not user:
            raise ValueError("Пользователь не найден или email уже подтвержден")

        # Генерируем новый токен
        new_token = ResendEmailService.generate_verification_token()

        user.verification_token = new_token
        user.verification_sent_at = datetime.utcnow()
        db.commit()

        # Отправляем email
        success = ResendEmailService.send_verification_email(
            db,
            email=email,
            verification_token=new_token,
            user_name=user.display_name
        )

        return success