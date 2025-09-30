import enum


from sqlalchemy.orm import relationship

from .associations import user_roles
from ..database import Base
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    ForeignKey,
    Date,
    Boolean,
    Enum,
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    verification_token = Column(String(100), nullable=True, index=True)
    verification_sent_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    # Дополнительные поля
    display_name = Column(String(255), nullable=True)
    image = Column(String(500), nullable=True)
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    about = Column(String(255), nullable=True)
    max_link_url = Column(String(255), nullable=True)

    p_office = relationship("ProjectOffice", back_populates="leader")
    event_types = relationship("EventType", back_populates="leader")

    achievements_given = relationship(
        "Achievement", back_populates="teacher", foreign_keys="Achievement.teacher_id"
    )
