"""
Video creation service using MoviePy + Pexels stock footage.
"""

import os
import uuid
import httpx
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from config import settings
from models import GeneratedVideo, Script, VideoStatus, ActivityLog
from services.voice_service import generate_voice
from services.thumbnail_service import generate_thumbnail

# MoviePy imports are heavy; import inside functions where needed.


async def search_pexels_videos(query: str, per_page: int = 5, orientation: str = "landscape") -> List[dict]:
    """Search Pexels for free stock videos."""
    if not settings.PEXELS_API_KEY:
        return []
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": settings.PEXELS_API_KEY}
    params = {"query": query, "per_page": per_page, "orientation": orientation}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = []
        for v in data.get("videos", []):
            # Prefer HD files
            files = sorted(
                v.get("video_files", []),
                key=lambda f: f.get("width", 0) * f.get("height", 0),
                reverse=True,
            )
            if files:
                best = files[0]
                results.append(
                    {
                        "id": v["id"],
                        "url": best["link"],
                        "width": best.get("width"),
                        "height": best.get("height"),
                        "duration": v.get("duration"),
                    }
                )
        return results


async def download_file(url: str, dest: Path) -> Path:
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
    return dest


def _create_color_clip(duration: float, size: tuple, color=(20, 30, 60)):
    from moviepy import ColorClip
    return ColorClip(size=size, color=color, duration=duration)


async def create_video_from_script(
    db: Session,
    user_id: int,
    script: Script,
    is_short: bool = False,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    pexels_query: Optional[str] = None,
    add_subtitles: bool = True,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> GeneratedVideo:
    """
    Full pipeline:
    1. Generate voiceover
    2. Fetch stock footage (or solid background fallback)
    3. Compose video with MoviePy
    4. Optional simple subtitles
    5. Generate thumbnail
    """
    from moviepy import (
        VideoFileClip,
        AudioFileClip,
        CompositeVideoClip,
        TextClip,
        concatenate_videoclips,
        ColorClip,
        ImageClip,
    )

    # Create DB record early
    video = GeneratedVideo(
        user_id=user_id,
        script_id=script.id,
        title=title or script.title or script.topic[:80],
        description=description or script.description,
        tags=tags or script.keywords or [],
        status=VideoStatus.DRAFT.value,
        is_short=is_short,
        width=settings.SHORTS_WIDTH if is_short else settings.DEFAULT_VIDEO_WIDTH,
        height=settings.SHORTS_HEIGHT if is_short else settings.DEFAULT_VIDEO_HEIGHT,
        voice_used=voice,
        pexels_query=pexels_query or script.topic,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    try:
        # 1. Voice
        video.status = VideoStatus.AUDIO_READY.value
        db.commit()
        voice_result = await generate_voice(
            text=script.content,
            voice=voice,
            rate=rate,
            pitch=pitch,
            filename=f"video_{video.id}_audio.mp3",
        )
        video.audio_path = voice_result["audio_path"]
        audio_duration = voice_result["duration_seconds"]

        # 2. Visuals
        target_w, target_h = video.width, video.height
        orientation = "portrait" if is_short else "landscape"
        query = pexels_query or script.topic or "technology abstract"

        stock_clips = []
        temp_files = []

        pexels_results = await search_pexels_videos(query, per_page=4, orientation=orientation)
        if pexels_results:
            for i, item in enumerate(pexels_results[:3]):
                try:
                    dest = settings.VIDEOS_DIR / f"temp_stock_{video.id}_{i}.mp4"
                    await download_file(item["url"], dest)
                    temp_files.append(dest)
                    clip = VideoFileClip(str(dest))
                    # Resize & crop to target aspect
                    clip = clip.resized(height=target_h) if clip.h < clip.w else clip.resized(width=target_w)
                    clip = clip.cropped(
                        x_center=clip.w / 2,
                        y_center=clip.h / 2,
                        width=min(clip.w, target_w),
                        height=min(clip.h, target_h),
                    )
                    if clip.w != target_w or clip.h != target_h:
                        clip = clip.resized((target_w, target_h))
                    stock_clips.append(clip)
                except Exception as e:
                    print(f"Stock clip error: {e}")
                    continue

        # Fallback solid + text if no stock
        if not stock_clips:
            bg = ColorClip(size=(target_w, target_h), color=(15, 23, 42), duration=audio_duration)
            stock_clips = [bg]

        # Loop / concatenate stock to cover audio duration
        total = 0.0
        final_clips = []
        idx = 0
        while total < audio_duration + 1:
            c = stock_clips[idx % len(stock_clips)]
            # Take a portion
            take = min(c.duration, audio_duration - total + 2)
            if take < 0.5:
                break
            part = c.subclipped(0, min(take, c.duration))
            final_clips.append(part)
            total += part.duration
            idx += 1
            if idx > 20:  # safety
                break

        if not final_clips:
            final_clips = [ColorClip(size=(target_w, target_h), color=(15, 23, 42), duration=audio_duration)]

        visual = concatenate_videoclips(final_clips, method="compose")
        if visual.duration > audio_duration:
            visual = visual.subclipped(0, audio_duration)
        elif visual.duration < audio_duration:
            # extend last frame
            last = visual.to_ImageClip(t=visual.duration - 0.1).with_duration(audio_duration - visual.duration)
            visual = concatenate_videoclips([visual, last])

        # 3. Audio
        audio = AudioFileClip(video.audio_path)
        visual = visual.with_audio(audio).with_duration(audio.duration)

        # 4. Simple title card / subtitles (basic)
        if add_subtitles and script.title:
            try:
                txt = TextClip(
                    text=script.title[:60],
                    font_size=48 if not is_short else 36,
                    color="white",
                    method="caption",
                    size=(target_w - 80, None),
                    text_align="center",
                )
                txt = txt.with_position(("center", 80 if not is_short else 120)).with_duration(min(5, audio.duration))
                visual = CompositeVideoClip([visual, txt])
            except Exception as e:
                print(f"Subtitle/title overlay skipped: {e}")

        # 5. Export
        out_name = f"video_{video.id}_{uuid.uuid4().hex[:8]}.mp4"
        out_path = settings.VIDEOS_DIR / out_name
        visual.write_videofile(
            str(out_path),
            fps=settings.DEFAULT_FPS,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="medium",
            logger=None,
        )

        # Cleanup temp
        visual.close()
        audio.close()
        for c in stock_clips:
            try:
                c.close()
            except Exception:
                pass
        for f in temp_files:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass

        video.video_path = str(out_path)
        video.duration_seconds = round(audio_duration, 2)
        video.has_subtitles = add_subtitles
        video.status = VideoStatus.VIDEO_READY.value

        # Thumbnail
        try:
            thumb_path = await generate_thumbnail(
                video_id=video.id,
                title=video.title,
                is_short=is_short,
            )
            video.thumbnail_path = thumb_path
            video.status = VideoStatus.THUMBNAIL_READY.value
        except Exception as e:
            print(f"Thumbnail error: {e}")

        db.add(
            ActivityLog(
                user_id=user_id,
                action="video_created",
                entity_type="video",
                entity_id=video.id,
                details={"title": video.title, "is_short": is_short},
            )
        )
        db.commit()
        db.refresh(video)
        return video

    except Exception as e:
        video.status = VideoStatus.FAILED.value
        video.error_message = str(e)[:500]
        db.commit()
        raise
