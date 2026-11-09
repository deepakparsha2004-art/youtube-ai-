"""Voice generation routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User, Script
from schemas import VoiceGenerateRequest, VoiceOut, VoiceListItem
from services.voice_service import generate_voice, list_voices, RECOMMENDED_VOICES
from routers.auth import get_current_user
from pathlib import Path

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.get("/voices", response_model=List[VoiceListItem])
async def get_voices():
    return await list_voices()


@router.get("/recommended")
def recommended():
    return RECOMMENDED_VOICES


@router.post("/generate", response_model=VoiceOut)
async def create_voice(
    request: VoiceGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    text = request.text
    if request.script_id:
        script = db.query(Script).filter(Script.id == request.script_id, Script.user_id == user.id).first()
        if not script:
            raise HTTPException(404, "Script not found")
        text = script.content
    result = await generate_voice(
        text=text,
        voice=request.voice,
        rate=request.rate,
        pitch=request.pitch,
    )
    return VoiceOut(**result)


@router.get("/audio/{filename}")
def serve_audio(filename: str, user: User = Depends(get_current_user)):
    from config import settings
    if Path(filename).name != filename:
        raise HTTPException(404, "Audio not found")
    path = settings.AUDIO_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "Audio not found")
    return FileResponse(path, media_type="audio/mpeg", filename=filename)
