from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.vitals import VitalType


class VitalReadingCreate(BaseModel):
    type: VitalType
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    glucose_mg_dl: Optional[float] = None
    glucose_context: Optional[str] = None
    value: Optional[float] = None
    notes: Optional[str] = None
    measured_at: Optional[datetime] = None


class VitalReadingOut(BaseModel):
    id: int
    type: VitalType
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    glucose_mg_dl: Optional[float] = None
    glucose_context: Optional[str] = None
    value: Optional[float] = None
    notes: Optional[str] = None
    measured_at: datetime

    class Config:
        from_attributes = True
