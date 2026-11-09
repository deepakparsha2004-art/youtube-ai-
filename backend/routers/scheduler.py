"""Automation scheduler routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, AutomationSchedule
from schemas import ScheduleCreate, ScheduleOut
from services.scheduler_service import create_schedule, toggle_schedule
from routers.auth import get_current_user

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@router.post("/", response_model=ScheduleOut)
def create(data: ScheduleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_schedule(db, user.id, data.model_dump())


@router.get("/", response_model=List[ScheduleOut])
def list_schedules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(AutomationSchedule)
        .filter(AutomationSchedule.user_id == user.id)
        .order_by(AutomationSchedule.created_at.desc())
        .all()
    )


@router.patch("/{schedule_id}/toggle", response_model=ScheduleOut)
def toggle(
    schedule_id: int,
    active: bool,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    schedule = db.query(AutomationSchedule).filter(
        AutomationSchedule.id == schedule_id, AutomationSchedule.user_id == user.id
    ).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    return toggle_schedule(db, schedule, active)


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    schedule = db.query(AutomationSchedule).filter(
        AutomationSchedule.id == schedule_id, AutomationSchedule.user_id == user.id
    ).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    db.delete(schedule)
    db.commit()
    return {"ok": True}
