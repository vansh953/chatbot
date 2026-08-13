from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)

    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)

    has_diabetes = Column(Boolean, default=False)
    has_hypertension = Column(Boolean, default=False)
    other_conditions = Column(String, nullable=True)  # comma separated free text
    allergies = Column(String, nullable=True)

    avatar_url = Column(String, nullable=True)  # hosted .glb URL from the avatar creator (e.g. Ready Player Me)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    vitals = relationship("VitalReading", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    diet_plans = relationship("DietPlan", back_populates="user", cascade="all, delete-orphan")
    schedule_items = relationship("ScheduleItem", back_populates="user", cascade="all, delete-orphan")
