"""
Simple automation scheduler (in-process, for local use).
For production use Celery + Redis or APScheduler with persistent jobs.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from models import AutomationSchedule, ActivityLog
from croniter import croniter


def calculate_next_run(cron_expression: str, base: Optional[datetime] = None) -> Optional[datetime]:
    if not cron_expression:
        return None
    try:
        base = base or datetime.utcnow()
        cron = croniter(cron_expression, base)
        return cron.get_next(datetime)
    except Exception:
        return None


def create_schedule(db: Session, user_id: int, data: dict) -> AutomationSchedule:
    next_run = calculate_next_run(data.get("cron_expression"))
    schedule = AutomationSchedule(
        user_id=user_id,
        name=data["name"],
        topic_template=data.get("topic_template"),
        script_type=data.get("script_type", "general"),
        is_short=data.get("is_short", False),
        voice=data.get("voice", "en-US-AriaNeural"),
        cron_expression=data.get("cron_expression"),
        next_run_at=next_run,
        is_active=data.get("is_active", True),
        config=data.get("config", {}),
    )
    db.add(schedule)
    db.add(
        ActivityLog(
            user_id=user_id,
            action="schedule_created",
            entity_type="schedule",
            details={"name": schedule.name},
        )
    )
    db.commit()
    db.refresh(schedule)
    return schedule


def toggle_schedule(db: Session, schedule: AutomationSchedule, active: bool) -> AutomationSchedule:
    schedule.is_active = active
    if active and schedule.cron_expression:
        schedule.next_run_at = calculate_next_run(schedule.cron_expression)
    db.commit()
    db.refresh(schedule)
    return schedule
