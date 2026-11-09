"""Analytics and activity logs."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import User, Script, GeneratedVideo, UploadHistory, AutomationSchedule, ActivityLog, VideoStatus
from schemas import DashboardStats, ActivityLogOut, ResearchResponse
from services.research_service import suggest_topics
from routers.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_scripts = db.query(func.count(Script.id)).filter(Script.user_id == user.id).scalar() or 0
    total_videos = db.query(func.count(GeneratedVideo.id)).filter(GeneratedVideo.user_id == user.id).scalar() or 0
    total_uploads = (
        db.query(func.count(UploadHistory.id))
        .join(GeneratedVideo)
        .filter(GeneratedVideo.user_id == user.id)
        .scalar()
        or 0
    )
    pending = (
        db.query(func.count(GeneratedVideo.id))
        .filter(
            GeneratedVideo.user_id == user.id,
            GeneratedVideo.status.in_([VideoStatus.THUMBNAIL_READY.value, VideoStatus.PENDING_APPROVAL.value]),
        )
        .scalar()
        or 0
    )
    active_schedules = (
        db.query(func.count(AutomationSchedule.id))
        .filter(AutomationSchedule.user_id == user.id, AutomationSchedule.is_active == True)
        .scalar()
        or 0
    )
    recent = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(15)
        .all()
    )
    return DashboardStats(
        total_scripts=total_scripts,
        total_videos=total_videos,
        total_uploads=total_uploads,
        pending_approvals=pending,
        active_schedules=active_schedules,
        recent_activity=[ActivityLogOut.model_validate(a) for a in recent],
    )


@router.get("/logs", response_model=List[ActivityLogOut])
def logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/research", response_model=ResearchResponse)
async def research(niche: str = "technology", count: int = 8, user: User = Depends(get_current_user)):
    return await suggest_topics(niche=niche, count=count)
