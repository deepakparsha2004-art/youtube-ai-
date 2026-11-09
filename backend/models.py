"""
SQLAlchemy models for the YouTube AI Automation Platform.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum
from database import Base


class VideoStatus(str, enum.Enum):
    DRAFT = "draft"
    SCRIPT_READY = "script_ready"
    AUDIO_READY = "audio_ready"
    VIDEO_READY = "video_ready"
    THUMBNAIL_READY = "thumbnail_ready"
    PENDING_APPROVAL = "pending_approval"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class Visibility(str, enum.Enum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class ScriptType(str, enum.Enum):
    SHORT = "short"
    LONG = "long"
    EDUCATIONAL = "educational"
    MOTIVATIONAL = "motivational"
    TECHNOLOGY = "technology"
    GENERAL = "general"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    channels = relationship("YouTubeChannel", back_populates="user")
    scripts = relationship("Script", back_populates="user")
    videos = relationship("GeneratedVideo", back_populates="user")
    schedules = relationship("AutomationSchedule", back_populates="user")
    logs = relationship("ActivityLog", back_populates="user")


class YouTubeChannel(Base):
    __tablename__ = "youtube_channels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel_id = Column(String(100), unique=True, index=True)
    channel_title = Column(String(255))
    channel_description = Column(Text, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    is_connected = Column(Boolean, default=False)
    subscriber_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="channels")
    uploads = relationship("UploadHistory", back_populates="channel")


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic = Column(String(500), nullable=False)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    script_type = Column(String(50), default=ScriptType.GENERAL.value)
    hashtags = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    word_count = Column(Integer, default=0)
    estimated_duration_seconds = Column(Integer, default=0)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="scripts")
    videos = relationship("GeneratedVideo", back_populates="script")


class GeneratedVideo(Base):
    __tablename__ = "generated_videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    status = Column(String(50), default=VideoStatus.DRAFT.value)
    is_short = Column(Boolean, default=False)
    width = Column(Integer, default=1920)
    height = Column(Integer, default=1080)
    duration_seconds = Column(Float, default=0.0)
    video_path = Column(String(500), nullable=True)
    audio_path = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    voice_used = Column(String(100), nullable=True)
    background_music = Column(String(200), nullable=True)
    has_subtitles = Column(Boolean, default=False)
    pexels_query = Column(String(200), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="videos")
    script = relationship("Script", back_populates="videos")
    uploads = relationship("UploadHistory", back_populates="video")


class UploadHistory(Base):
    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("generated_videos.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("youtube_channels.id"), nullable=False)
    youtube_video_id = Column(String(50), nullable=True)
    youtube_url = Column(String(300), nullable=True)
    visibility = Column(String(20), default=Visibility.PRIVATE.value)
    scheduled_publish_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)
    approved_by_user = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("GeneratedVideo", back_populates="uploads")
    channel = relationship("YouTubeChannel", back_populates="uploads")


class AutomationSchedule(Base):
    __tablename__ = "automation_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    topic_template = Column(String(500), nullable=True)
    script_type = Column(String(50), default=ScriptType.GENERAL.value)
    is_short = Column(Boolean, default=False)
    voice = Column(String(100), default="en-US-AriaNeural")
    cron_expression = Column(String(100), nullable=True)  # e.g. "0 9 * * *"
    next_run_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    last_status = Column(String(50), nullable=True)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="schedules")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logs")
