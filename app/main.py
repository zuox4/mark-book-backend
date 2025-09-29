from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy.orm import Session

from app.admin import setup_admin
from app.database.database import engine, get_db
from app.database import Base
from app.routes import admin_router, api_router

# Импортируем все модели чтобы они зарегистрировались
from app.database.models import (
    users,
    project_offices,
    groups,
    event_types,
    events,
    achievements,
)
from app.services.resend_email_service import ResendEmailService

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Educational Achievement Platform",
    description="API для управления образовательными достижениями",
    version="1.0.0",
)
admin = setup_admin(app)
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn



    uvicorn.run(app, host="0.0.0.0", port=8000)
