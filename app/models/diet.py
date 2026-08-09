from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class DietPlan(Base):
    __tablename__ = "diet_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    plan = Column(JSON, nullable=False)  # structured plan: {days: [{meals: [...]}]}
    goal = Column(String, nullable=True)  # e.g. "diabetes-friendly", "weight-loss"
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="diet_plans")


class ScheduleItem(Base):
    """A recurring reminder: medication, meal, glucose check, exercise, etc."""

    __tablename__ = "schedule_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    category = Column(String, nullable=False)  # medication / meal / vitals_check / exercise
    time_of_day = Column(String, nullable=False)  # "08:00"
    frequency = Column(String, default="daily")  # daily / weekdays / custom
    notes = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="schedule_items")
