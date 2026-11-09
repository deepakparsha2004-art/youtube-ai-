"""App settings routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, Setting
from schemas import SettingUpdate, SettingOut
from routers.auth import get_current_user
from services.ollama_service import ollama_service
from config import settings as app_settings

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/status")
async def system_status(user: User = Depends(get_current_user)):
    ollama_ok = await ollama_service.is_available()
    models = await ollama_service.list_models() if ollama_ok else []
    return {
        "ollama_available": ollama_ok,
        "ollama_model": app_settings.OLLAMA_MODEL,
        "available_models": models,
        "pexels_configured": bool(app_settings.PEXELS_API_KEY),
        "fal_video_configured": bool(app_settings.FAL_KEY and app_settings.FAL_VIDEO_ENABLED),
        "fal_video_model": app_settings.FAL_VIDEO_MODEL,
        "google_oauth_configured": bool(app_settings.GOOGLE_CLIENT_ID and app_settings.GOOGLE_CLIENT_SECRET),
        "app_version": app_settings.APP_VERSION,
    }


@router.get("/", response_model=list[SettingOut])
def get_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Setting).all()


@router.put("/")
def update_setting(data: SettingUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Setting).filter(Setting.key == data.key).first()
    if not s:
        s = Setting(key=data.key, value=data.value)
        db.add(s)
    else:
        s.value = data.value
    db.commit()
    return {"ok": True, "key": data.key}
