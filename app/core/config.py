import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    # DATABASE_URL: str = os.getenv("DATABASE_URL")

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

    DB_HOST: str = os.getenv("DB_HOST")  # Например: "192.168.1.100"
    DB_PORT: int = os.getenv("DB_PORT")
    DB_NAME: str = os.getenv("DB_NAME")  # Например: "myapp_db"
    DB_USER: str = os.getenv("DB_USER")  # Например: "remote_user"
    DB_PASSWORD : str = os.getenv("DB_PASSWORD")  # Например: "secure_password123"
settings = Settings()