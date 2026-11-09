"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Any, Dict, Literal
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# ---------- Auth / User ----------
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Scripts ----------
class ScriptGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    script_type: str = "general"  # short, long, educational, motivational, technology, general
    length: str = "medium"  # short (~60s), medium (~3-5min), long (~8-12min)
    tone: str = "engaging"
    include_hooks: bool = True
    generate_title: bool = True
    generate_description: bool = True
    generate_hashtags: bool = True


class ScriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic: str
    title: Optional[str]
    description: Optional[str]
    content: str
    script_type: str
    hashtags: List[str] = []
    keywords: List[str] = []
    word_count: int
    estimated_duration_seconds: int
    model_used: Optional[str]
    created_at: datetime


class ScriptUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    hashtags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


# ---------- Voice ----------
class VoiceGenerateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice: str = "en-US-AriaNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    script_id: Optional[int] = None


class VoiceOut(BaseModel):
    audio_path: str
    filename: str
    duration_seconds: Optional[float] = None
    voice: str


class VoiceListItem(BaseModel):
    name: str
    gender: str
    locale: str
    short_name: str


# ---------- Video ----------
class VideoCreateRequest(BaseModel):
    script_id: int
    is_short: bool = False
    voice: str = "en-US-AriaNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    pexels_query: Optional[str] = None
    add_subtitles: bool = True
    add_background_music: bool = False
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class FalVideoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=2000)
    title: Optional[str] = Field(default=None, max_length=200)
    is_short: bool = False
    duration: Literal["4s", "6s", "8s"] = "8s"
    generate_audio: bool = False


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: Optional[str]
    tags: List[str] = []
    status: str
    is_short: bool
    width: int
    height: int
    duration_seconds: float
    video_path: Optional[str]
    audio_path: Optional[str]
    thumbnail_path: Optional[str]
    voice_used: Optional[str]
    has_subtitles: bool
    error_message: Optional[str]
    created_at: datetime
    script_id: Optional[int]


class ThumbnailRequest(BaseModel):
    video_id: int
    title: Optional[str] = None
    style: str = "modern"  # modern, bold, minimal, tech
    background_color: Optional[str] = None


# ---------- YouTube ----------
class YouTubeChannelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel_id: Optional[str]
    channel_title: Optional[str]
    channel_description: Optional[str]
    thumbnail_url: Optional[str]
    is_connected: bool
    subscriber_count: int
    video_count: int
    view_count: int


class UploadRequest(BaseModel):
    video_id: int
    channel_id: int
    visibility: str = "private"  # private, unlisted, public
    scheduled_publish_at: Optional[datetime] = None
    approve: bool = False  # must be True to allow public


class UploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    video_id: int
    channel_id: int
    youtube_video_id: Optional[str]
    youtube_url: Optional[str]
    visibility: str
    scheduled_publish_at: Optional[datetime]
    status: str
    error_message: Optional[str]
    approved_by_user: bool
    uploaded_at: Optional[datetime]
    created_at: datetime


# ---------- Scheduler ----------
class ScheduleCreate(BaseModel):
    name: str
    topic_template: Optional[str] = None
    script_type: str = "general"
    is_short: bool = False
    voice: str = "en-US-AriaNeural"
    cron_expression: Optional[str] = None  # "0 9 * * *" daily at 9am
    is_active: bool = True
    config: Dict[str, Any] = {}


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    topic_template: Optional[str]
    script_type: str
    is_short: bool
    voice: str
    cron_expression: Optional[str]
    next_run_at: Optional[datetime]
    is_active: bool
    last_run_at: Optional[datetime]
    last_status: Optional[str]
    config: Dict[str, Any]
    created_at: datetime


# ---------- Research ----------
class TopicSuggestion(BaseModel):
    topic: str
    reason: str
    estimated_interest: str
    keywords: List[str] = []


class ResearchResponse(BaseModel):
    suggestions: List[TopicSuggestion]
    generated_at: datetime


# ---------- Analytics / Logs ----------
class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    details: Dict[str, Any]
    created_at: datetime


class DashboardStats(BaseModel):
    total_scripts: int
    total_videos: int
    total_uploads: int
    pending_approvals: int
    active_schedules: int
    recent_activity: List[ActivityLogOut]


# ---------- Settings ----------
class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    value: Optional[str]
    description: Optional[str]
