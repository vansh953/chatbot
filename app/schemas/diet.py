from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class DietPlanGenerateRequest(BaseModel):
    goal: Optional[str] = None  # e.g. "diabetes-friendly", "low-sodium", "weight-loss"
    days: int = 7
    extra_notes: Optional[str] = None


class DietPlanOut(BaseModel):
    id: int
    plan: Any
    goal: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleItemCreate(BaseModel):
    title: str
    category: str  # medication / meal / vitals_check / exercise
    time_of_day: str  # "08:00"
    frequency: str = "daily"
    notes: Optional[str] = None


class ScheduleItemOut(BaseModel):
    id: int
    title: str
    category: str
    time_of_day: str
    frequency: str
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
