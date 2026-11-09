"""
YouTube Data API v3 integration with Google OAuth2.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from config import settings
from models import YouTubeChannel, UploadHistory, GeneratedVideo, VideoStatus, Visibility, ActivityLog


SCOPES = settings.YOUTUBE_SCOPES.split()


def get_oauth_flow(state: Optional[str] = None) -> Flow:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth credentials not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")

    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow


def get_authorization_url(state: str = "youtube_connect") -> str:
    flow = get_oauth_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return auth_url


def exchange_code(code: str) -> Credentials:
    flow = get_oauth_flow()
    flow.fetch_token(code=code)
    return flow.credentials


def credentials_to_dict(creds: Credentials) -> dict:
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }


def credentials_from_channel(channel: YouTubeChannel) -> Credentials:
    return Credentials(
        token=channel.access_token,
        refresh_token=channel.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )


def save_channel_tokens(db: Session, user_id: int, creds: Credentials) -> YouTubeChannel:
    youtube = build("youtube", "v3", credentials=creds)
    response = youtube.channels().list(part="snippet,statistics", mine=True).execute()
    items = response.get("items", [])
    if not items:
        raise ValueError("No YouTube channel found for this Google account")

    info = items[0]
    snippet = info["snippet"]
    stats = info.get("statistics", {})

    channel = db.query(YouTubeChannel).filter(YouTubeChannel.user_id == user_id).first()
    if not channel:
        channel = YouTubeChannel(user_id=user_id)
        db.add(channel)

    channel.channel_id = info["id"]
    channel.channel_title = snippet.get("title")
    channel.channel_description = snippet.get("description")
    channel.thumbnail_url = snippet.get("thumbnails", {}).get("default", {}).get("url")
    channel.access_token = creds.token
    channel.refresh_token = creds.refresh_token or channel.refresh_token
    channel.token_expiry = creds.expiry
    channel.is_connected = True
    channel.subscriber_count = int(stats.get("subscriberCount", 0))
    channel.video_count = int(stats.get("videoCount", 0))
    channel.view_count = int(stats.get("viewCount", 0))
    db.commit()
    db.refresh(channel)
    return channel


def get_youtube_client(channel: YouTubeChannel):
    creds = credentials_from_channel(channel)
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        channel.access_token = creds.token
        channel.token_expiry = creds.expiry
    return build("youtube", "v3", credentials=creds)


async def upload_video(
    db: Session,
    video: GeneratedVideo,
    channel: YouTubeChannel,
    visibility: str = "private",
    scheduled_publish_at: Optional[datetime] = None,
    approved: bool = False,
) -> UploadHistory:
    """
    Upload a video to YouTube.
    Public uploads require approved=True for safety.
    """
    if visibility == "public" and not approved:
        raise ValueError("Public uploads require explicit user approval (approve=True)")

    if not video.video_path or not Path(video.video_path).exists():
        raise ValueError("Video file not found")

    upload = UploadHistory(
        video_id=video.id,
        channel_id=channel.id,
        visibility=visibility,
        scheduled_publish_at=scheduled_publish_at,
        status="uploading",
        approved_by_user=approved,
    )
    db.add(upload)
    video.status = VideoStatus.UPLOADING.value
    db.commit()
    db.refresh(upload)

    try:
        youtube = get_youtube_client(channel)

        body: Dict[str, Any] = {
            "snippet": {
                "title": video.title[:100],
                "description": (video.description or "")[:5000],
                "tags": (video.tags or [])[:15],
                "categoryId": "22",  # People & Blogs (change as needed)
            },
            "status": {
                "privacyStatus": visibility if visibility != "public" or approved else "private",
                "selfDeclaredMadeForKids": False,
            },
        }

        if scheduled_publish_at and visibility != "public":
            # YouTube requires publishAt only with private
            body["status"]["privacyStatus"] = "private"
            body["status"]["publishAt"] = scheduled_publish_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        media = MediaFileUpload(
            video.video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 8,
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")

        yt_id = response["id"]
        upload.youtube_video_id = yt_id
        upload.youtube_url = f"https://www.youtube.com/watch?v={yt_id}"
        upload.status = "uploaded"
        upload.uploaded_at = datetime.utcnow()

        # Set thumbnail if available
        if video.thumbnail_path and Path(video.thumbnail_path).exists():
            try:
                youtube.thumbnails().set(
                    videoId=yt_id,
                    media_body=MediaFileUpload(video.thumbnail_path),
                ).execute()
            except Exception as e:
                print(f"Thumbnail upload warning: {e}")

        video.status = VideoStatus.UPLOADED.value
        if scheduled_publish_at:
            video.status = VideoStatus.SCHEDULED.value

        db.add(
            ActivityLog(
                user_id=video.user_id,
                action="video_uploaded",
                entity_type="upload",
                entity_id=upload.id,
                details={"youtube_id": yt_id, "visibility": visibility},
            )
        )
        db.commit()
        db.refresh(upload)
        return upload

    except HttpError as e:
        upload.status = "failed"
        upload.error_message = str(e)[:500]
        video.status = VideoStatus.FAILED.value
        video.error_message = str(e)[:500]
        db.commit()
        raise
    except Exception as e:
        upload.status = "failed"
        upload.error_message = str(e)[:500]
        video.status = VideoStatus.FAILED.value
        video.error_message = str(e)[:500]
        db.commit()
        raise
