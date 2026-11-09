"""YouTube OAuth and upload routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User, YouTubeChannel, GeneratedVideo, UploadHistory
from schemas import YouTubeChannelOut, UploadRequest, UploadOut
from services.youtube_service import (
    get_authorization_url,
    exchange_code,
    save_channel_tokens,
    upload_video,
)
from routers.auth import get_current_user
from config import settings
from utils.security import create_youtube_oauth_state, decode_access_token

router = APIRouter(prefix="/youtube", tags=["YouTube"])


@router.get("/connect")
def connect_youtube(user: User = Depends(get_current_user)):
    """Return Google OAuth URL for connecting a YouTube channel."""
    try:
        url = get_authorization_url(state=create_youtube_oauth_state(int(user.id)))
        return {"authorization_url": url}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/oauth/callback")
def oauth_callback(
    code: str = Query(...),
    state: str = Query(None),
    db: Session = Depends(get_db),
):
    """Google redirects here after consent."""
    try:
        state_payload = decode_access_token(state or "")
        if not state_payload or state_payload.get("purpose") != "youtube_oauth":
            raise ValueError("Invalid or expired OAuth state")
        user_id = state_payload.get("sub")
        if not user_id or not str(user_id).isdigit():
            raise ValueError("Invalid OAuth state")

        creds = exchange_code(code)
        channel = save_channel_tokens(db, int(user_id), creds)
        # Redirect to frontend
        return RedirectResponse(f"{settings.FRONTEND_URL}/youtube?connected=1&channel={channel.channel_title}")
    except Exception as e:
        return RedirectResponse(f"{settings.FRONTEND_URL}/youtube?error={str(e)[:100]}")


@router.get("/channel", response_model=YouTubeChannelOut)
def get_channel(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = db.query(YouTubeChannel).filter(YouTubeChannel.user_id == user.id).first()
    if not channel:
        raise HTTPException(404, "No YouTube channel connected")
    return channel


@router.get("/channels", response_model=List[YouTubeChannelOut])
def list_channels(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(YouTubeChannel).filter(YouTubeChannel.user_id == user.id).all()


@router.post("/upload", response_model=UploadOut)
async def upload(
    request: UploadRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    video = db.query(GeneratedVideo).filter(
        GeneratedVideo.id == request.video_id, GeneratedVideo.user_id == user.id
    ).first()
    if not video:
        raise HTTPException(404, "Video not found")
    channel = db.query(YouTubeChannel).filter(
        YouTubeChannel.id == request.channel_id, YouTubeChannel.user_id == user.id
    ).first()
    if not channel or not channel.is_connected:
        raise HTTPException(400, "YouTube channel not connected")

    upload_rec = await upload_video(
        db=db,
        video=video,
        channel=channel,
        visibility=request.visibility,
        scheduled_publish_at=request.scheduled_publish_at,
        approved=request.approve,
    )
    return upload_rec


@router.get("/uploads", response_model=List[UploadOut])
def list_uploads(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(UploadHistory)
        .join(GeneratedVideo)
        .filter(GeneratedVideo.user_id == user.id)
        .order_by(UploadHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.delete("/disconnect")
def disconnect(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    channel = db.query(YouTubeChannel).filter(YouTubeChannel.user_id == user.id).first()
    if channel:
        channel.is_connected = False
        channel.access_token = None
        channel.refresh_token = None
        db.commit()
    return {"ok": True}
