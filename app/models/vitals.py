import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class VitalType(str, enum.Enum):
    blood_pressure = "blood_pressure"
    blood_glucose = "blood_glucose"
    sleep_hours = "sleep_hours"
    heart_rate = "heart_rate"


class VitalReading(Base):
    __tablename__ = "vital_readings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    type = Column(Enum(VitalType), nullable=False)

    # Blood pressure
    systolic = Column(Integer, nullable=True)
    diastolic = Column(Integer, nullable=True)

    # Blood glucose (mg/dL)
    glucose_mg_dl = Column(Float, nullable=True)
    glucose_context = Column(String, nullable=True)  # fasting / post_meal / random

    # Sleep hours / heart rate (bpm) — generic numeric value
    value = Column(Float, nullable=True)

    notes = Column(String, nullable=True)
    measured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="vitals")