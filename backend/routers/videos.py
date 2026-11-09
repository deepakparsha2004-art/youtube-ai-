"""Video creation and management routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models import ActivityLog, User, Script, GeneratedVideo, VideoStatus
from schemas import FalVideoGenerateRequest, VideoCreateRequest, VideoOut, ThumbnailRequest
from services.video_service import create_video_from_script
from services.fal_video_service import FalVideoError, generate_fal_video
from services.thumbnail_service import generate_thumbnail
from routers.auth import get_current_user
from pathlib import Path
from config import settings
import httpx
import logging

router = APIRouter(prefix="/videos", tags=["Videos"])
logger = logging.getLogger(__name__)


@router.post("/create", response_model=VideoOut)
async def create_video(
    request: VideoCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    script = db.query(Script).filter(Script.id == request.script_id, Script.user_id == user.id).first()
    if not script:
        raise HTTPException(404, "Script not found")
    video = await create_video_from_script(
        db=db,
        user_id=user.id,
        script=script,
        is_short=request.is_short,
        voice=request.voice,
        rate=request.rate,
        pitch=request.pitch,
        pexels_query=request.pexels_query,
        add_subtitles=request.add_subtitles,
        title=request.title,
        description=request.description,
        tags=request.tags,
    )
    return video


@router.post("/generate-ai", response_model=VideoOut)
async def generate_ai_video(
    request: FalVideoGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not settings.FAL_VIDEO_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="fal.ai video generation is disabled. Configure a rotated FAL_KEY and set FAL_VIDEO_ENABLED=true.",
        )
    if not settings.FAL_KEY:
        raise HTTPException(
            status_code=503,
            detail="fal.ai is not configured. Set FAL_KEY in backend/.env and restart the backend.",
        )

    is_short = request.is_short
    title = request.title or request.prompt[:80]
    video = GeneratedVideo(
        user_id=user.id,
        title=title,
        status=VideoStatus.DRAFT.value,
        is_short=is_short,
        width=720 if is_short else 1280,
        height=1280 if is_short else 720,
        duration_seconds=int(request.duration[:-1]),
        has_subtitles=False,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    try:
        video_path, duration = await generate_fal_video(
            prompt=request.prompt,
            is_short=is_short,
            duration=request.duration,
            generate_audio=request.generate_audio,
        )
        db.query(GeneratedVideo).filter(GeneratedVideo.id == video.id).update(
            {
                "video_path": str(video_path),
                "duration_seconds": float(duration),
                "status": VideoStatus.VIDEO_READY.value,
            },
            synchronize_session=False,
        )

        db.add(
            ActivityLog(
                user_id=user.id,
                action="video_generated_with_fal",
                entity_type="video",
                entity_id=video.id,
                details={"title": video.title, "model": settings.FAL_VIDEO_MODEL},
            )
        )
        db.commit()
        db.refresh(video)
        return video
    except FalVideoError as exc:
        db.query(GeneratedVideo).filter(GeneratedVideo.id == video.id).update(
            {"status": VideoStatus.FAILED.value, "error_message": exc.detail[:500]},
            synchronize_session=False,
        )
        db.commit()
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except httpx.RequestError as exc:
        logger.warning("fal.ai request failed for video %s: %s", video.id, type(exc).__name__)
        error_message = "Could not connect to fal.ai."
        db.query(GeneratedVideo).filter(GeneratedVideo.id == video.id).update(
            {"status": VideoStatus.FAILED.value, "error_message": error_message},
            synchronize_session=False,
        )
        db.commit()
        raise HTTPException(status_code=502, detail=error_message) from exc
    except OSError as exc:
        logger.exception("Could not save fal.ai video %s", video.id)
        error_message = "Could not save the generated video locally."
        db.query(GeneratedVideo).filter(GeneratedVideo.id == video.id).update(
            {"status": VideoStatus.FAILED.value, "error_message": error_message},
            synchronize_session=False,
        )
        db.commit()
        raise HTTPException(status_code=500, detail=error_message) from exc


@router.get("/", response_model=List[VideoOut])
def list_videos(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(GeneratedVideo)
        .filter(GeneratedVideo.user_id == user.id)
        .order_by(GeneratedVideo.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{video_id}", response_model=VideoOut)
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    video = db.query(GeneratedVideo).filter(GeneratedVideo.id == video_id, GeneratedVideo.user_id == user.id).first()
    if not video:
        raise HTTPException(404, "Video not found")
    return video


@router.post("/{video_id}/thumbnail", response_model=VideoOut)
async def create_thumbnail(
    video_id: int,
    request: ThumbnailRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    video = db.query(GeneratedVideo).filter(GeneratedVideo.id == video_id, GeneratedVideo.user_id == user.id).first()
    if not video:
        raise HTTPException(404, "Video not found")
    path = await generate_thumbnail(
        video_id=video.id,
        title=request.title or video.title,
        is_short=video.is_short,
        style=request.style,
        background_color=request.background_color,
    )
    video.thumbnail_path = path
    db.commit()
    db.refresh(video)
    return video


@router.get("/{video_id}/file")
def serve_video(video_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.query(GeneratedVideo).filter(GeneratedVideo.id == video_id, GeneratedVideo.user_id == user.id).first()
    if not video or not video.video_path:
        raise HTTPException(404, "Video file not found")
    path = Path(video.video_path)
    if not path.exists():
        raise HTTPException(404, "File missing on disk")
    return FileResponse(path, media_type="video/mp4", filename=path.name)


@router.get("/{video_id}/thumbnail-file")
def serve_thumbnail(video_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.query(GeneratedVideo).filter(GeneratedVideo.id == video_id, GeneratedVideo.user_id == user.id).first()
    if not video or not video.thumbnail_path:
        raise HTTPException(404, "Thumbnail not found")
    path = Path(video.thumbnail_path)
    if not path.exists():
        raise HTTPException(404, "File missing")
    return FileResponse(path, media_type="image/png")


@router.delete("/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    video = db.query(GeneratedVideo).filter(GeneratedVideo.id == video_id, GeneratedVideo.user_id == user.id).first()
    if not video:
        raise HTTPException(404, "Video not found")
    db.delete(video)
    db.commit()
    return {"ok": True}
