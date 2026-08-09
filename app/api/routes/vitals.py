from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.vitals import VitalReading, VitalType
from app.schemas.vitals import VitalReadingCreate, VitalReadingOut

router = APIRouter(prefix="/vitals", tags=["vitals"])


@router.post("", response_model=VitalReadingOut, status_code=201)
def add_vital(
    payload: VitalReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reading = VitalReading(
        user_id=current_user.id,
        measured_at=payload.measured_at or datetime.now(timezone.utc),
        **payload.model_dump(exclude={"measured_at"}),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("", response_model=list[VitalReadingOut])
def list_vitals(
    type: Optional[VitalType] = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(VitalReading).filter(VitalReading.user_id == current_user.id)
    if type:
        q = q.filter(VitalReading.type == type)
    return q.order_by(VitalReading.measured_at.desc()).limit(limit).all()


@router.get("/summary")
def vitals_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Latest reading + simple average of last 7 for glucose and BP — handy for dashboards
    and for feeding context into the diet-plan generator."""
    latest_glucose = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == current_user.id, VitalReading.type == VitalType.blood_glucose)
        .order_by(VitalReading.measured_at.desc())
        .first()
    )
    latest_bp = (
        db.query(VitalReading)
        .filter(VitalReading.user_id == current_user.id, VitalReading.type == VitalType.blood_pressure)
        .order_by(VitalReading.measured_at.desc())
        .first()
    )
    return {
        "latest_glucose": {
            "value": latest_glucose.glucose_mg_dl if latest_glucose else None,
            "context": latest_glucose.glucose_context if latest_glucose else None,
            "measured_at": latest_glucose.measured_at if latest_glucose else None,
        },
        "latest_blood_pressure": {
            "systolic": latest_bp.systolic if latest_bp else None,
            "diastolic": latest_bp.diastolic if latest_bp else None,
            "measured_at": latest_bp.measured_at if latest_bp else None,
        },
    }


@router.delete("/{vital_id}", status_code=204)
def delete_vital(
    vital_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    reading = (
        db.query(VitalReading)
        .filter(VitalReading.id == vital_id, VitalReading.user_id == current_user.id)
        .first()
    )
    if reading:
        db.delete(reading)
        db.commit()
