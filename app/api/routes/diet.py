from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.diet import DietPlan, ScheduleItem
from app.models.user import User
from app.schemas.diet import (
    DietPlanGenerateRequest,
    DietPlanOut,
    ScheduleItemCreate,
    ScheduleItemOut,
)
from app.services.groq_service import build_user_context, generate_diet_plan

router = APIRouter(tags=["diet & schedule"])


@router.post("/diet/generate", response_model=DietPlanOut)
def create_diet_plan(
    payload: DietPlanGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = payload.goal
    if not goal:
        if current_user.has_diabetes and current_user.has_hypertension:
            goal = "diabetes-friendly and low-sodium"
        elif current_user.has_diabetes:
            goal = "diabetes-friendly"
        elif current_user.has_hypertension:
            goal = "low-sodium"
        else:
            goal = "general balanced health"

    try:
        plan_json = generate_diet_plan(
            user_context=build_user_context(current_user),
            goal=goal,
            days=payload.days,
            extra_notes=payload.extra_notes or "",
            language=payload.language,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to generate diet plan: {e}")

    # Deactivate previous plans, save new one as active
    db.query(DietPlan).filter(DietPlan.user_id == current_user.id, DietPlan.is_active == True).update(
        {"is_active": False}
    )
    plan = DietPlan(user_id=current_user.id, plan=plan_json, goal=goal, is_active=True)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/diet/current", response_model=DietPlanOut)
def get_current_plan(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = (
        db.query(DietPlan)
        .filter(DietPlan.user_id == current_user.id, DietPlan.is_active == True)
        .order_by(DietPlan.created_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No active diet plan. Generate one first.")
    return plan


@router.get("/diet/history", response_model=list[DietPlanOut])
def get_plan_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(DietPlan)
        .filter(DietPlan.user_id == current_user.id)
        .order_by(DietPlan.created_at.desc())
        .all()
    )


# ---- Schedule / reminders (medication, meals, vitals checks, exercise) ----


@router.post("/schedule", response_model=ScheduleItemOut, status_code=201)
def create_schedule_item(
    payload: ScheduleItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = ScheduleItem(user_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/schedule", response_model=list[ScheduleItemOut])
def list_schedule_items(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return (
        db.query(ScheduleItem)
        .filter(ScheduleItem.user_id == current_user.id, ScheduleItem.is_active == True)
        .order_by(ScheduleItem.time_of_day.asc())
        .all()
    )


@router.delete("/schedule/{item_id}", status_code=204)
def delete_schedule_item(
    item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    item = (
        db.query(ScheduleItem)
        .filter(ScheduleItem.id == item_id, ScheduleItem.user_id == current_user.id)
        .first()
    )
    if item:
        db.delete(item)
        db.commit()
