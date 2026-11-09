"""
Configuration module for YouTube AI Automation Platform.
Loads environment variables and provides centralized settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "YouTube AI Command Center"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "change-this-to-a-long-random-secret-key-in-production"
    DEFAULT_USERNAME: str = "admin"
    DEFAULT_PASSWORD: str = "Admin@123"
    DEFAULT_EMAIL: str = "admin@youtubeai.local"
    ALLOW_GUEST_ACCESS: bool = True
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = "sqlite:///./youtube_ai.db"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"  # or mistral, phi3, etc.

    # Edge TTS
    DEFAULT_VOICE: str = "en-US-AriaNeural"
    DEFAULT_RATE: str = "+0%"
    DEFAULT_PITCH: str = "+0Hz"

    # Pexels (stock footage)
    PEXELS_API_KEY: Optional[str] = None

    # fal.ai
    FAL_KEY: Optional[str] = None
    FAL_VIDEO_ENABLED: bool = False
    FAL_VIDEO_MODEL: str = "fal-ai/veo3.1/fast"
    FAL_VIDEO_TIMEOUT_SECONDS: int = 600

    # YouTube / Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/youtube/oauth/callback"
    GOOGLE_LOGIN_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    YOUTUBE_SCOPES: str = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/youtube"

    # GitHub OAuth sign-in
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/github/callback"

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    GENERATED_DIR: Path = BASE_DIR / "generated"
    SCRIPTS_DIR: Path = GENERATED_DIR / "scripts"
    AUDIO_DIR: Path = GENERATED_DIR / "audio"
    VIDEOS_DIR: Path = GENERATED_DIR / "videos"
    THUMBNAILS_DIR: Path = GENERATED_DIR / "thumbnails"
    UPLOADS_DIR: Path = BASE_DIR / "uploads"

    # Video defaults
    DEFAULT_VIDEO_WIDTH: int = 1920
    DEFAULT_VIDEO_HEIGHT: int = 1080
    SHORTS_WIDTH: int = 1080
    SHORTS_HEIGHT: int = 1920
    DEFAULT_FPS: int = 30

    # Frontend CORS
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    # Ensure directories exist
    for d in [
        settings.SCRIPTS_DIR,
        settings.AUDIO_DIR,
        settings.VIDEOS_DIR,
        settings.THUMBNAILS_DIR,
        settings.UPLOADS_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
