"""
AI Voice generation using Microsoft Edge TTS (free, high quality).
"""

import edge_tts
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from config import settings
from schemas import VoiceListItem
import uuid


# Popular high-quality voices
RECOMMENDED_VOICES = [
    {"name": "Aria (US Female)", "short_name": "en-US-AriaNeural", "gender": "Female", "locale": "en-US"},
    {"name": "Jenny (US Female)", "short_name": "en-US-JennyNeural", "gender": "Female", "locale": "en-US"},
    {"name": "Guy (US Male)", "short_name": "en-US-GuyNeural", "gender": "Male", "locale": "en-US"},
    {"name": "Christopher (US Male)", "short_name": "en-US-ChristopherNeural", "gender": "Male", "locale": "en-US"},
    {"name": "Sonia (UK Female)", "short_name": "en-GB-SoniaNeural", "gender": "Female", "locale": "en-GB"},
    {"name": "Ryan (UK Male)", "short_name": "en-GB-RyanNeural", "gender": "Male", "locale": "en-GB"},
    {"name": "Natasha (AU Female)", "short_name": "en-AU-NatashaNeural", "gender": "Female", "locale": "en-AU"},
    {"name": "William (AU Male)", "short_name": "en-AU-WilliamNeural", "gender": "Male", "locale": "en-AU"},
    {"name": "Neerja (IN Female)", "short_name": "en-IN-NeerjaNeural", "gender": "Female", "locale": "en-IN"},
    {"name": "Prabhat (IN Male)", "short_name": "en-IN-PrabhatNeural", "gender": "Male", "locale": "en-IN"},
]


async def list_voices() -> List[VoiceListItem]:
    try:
        voices = await edge_tts.list_voices()
        result = []
        for v in voices:
            if v["Locale"].startswith("en-"):
                result.append(
                    VoiceListItem(
                        name=v.get("FriendlyName", v["ShortName"]),
                        gender=v.get("Gender", "Unknown"),
                        locale=v["Locale"],
                        short_name=v["ShortName"],
                    )
                )
        return result
    except Exception:
        # Fallback to recommended
        return [
            VoiceListItem(
                name=v["name"],
                gender=v["gender"],
                locale=v["locale"],
                short_name=v["short_name"],
            )
            for v in RECOMMENDED_VOICES
        ]


async def generate_voice(
    text: str,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    filename: Optional[str] = None,
) -> dict:
    """
    Generate MP3 audio from text using Edge TTS.
    Returns path info.
    """
    if not filename:
        filename = f"voice_{uuid.uuid4().hex[:12]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp3"
    output_path = settings.AUDIO_DIR / filename

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(output_path))

    # Approximate duration (Edge TTS does not return it easily; estimate ~150 wpm)
    word_count = len(text.split())
    duration = max(1.0, (word_count / 150.0) * 60.0)

    return {
        "audio_path": str(output_path),
        "filename": filename,
        "duration_seconds": round(duration, 2),
        "voice": voice,
    }
