import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # School Info
    SCHOOL_NAME: str = os.getenv("SCHOOL_NAME")
    SCHOOL_DOMAIN: str = os.getenv("SCHOOL_DOMAIN")

    # Resend Email Service
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL")

    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")

    # Verification
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24


settings = Settings()