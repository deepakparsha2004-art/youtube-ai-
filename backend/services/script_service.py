"""
Script generation service using Ollama.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from services.ollama_service import ollama_service
from models import Script, ActivityLog
from schemas import ScriptGenerateRequest
from config import settings
import re


SYSTEM_PROMPT = """You are an expert YouTube scriptwriter and content strategist.
You create engaging, high-retention scripts optimized for YouTube algorithms.
Always write in a conversational, energetic style suitable for spoken narration.
Include natural pauses and emphasis where appropriate.
Never use markdown formatting in the script body itself."""


def estimate_duration(word_count: int) -> int:
    """Rough estimate: ~150 words per minute for spoken content."""
    return max(30, int((word_count / 150) * 60))


def extract_hashtags(text: str) -> List[str]:
    return list(set(re.findall(r"#\w+", text)))


async def generate_script(
    db: Session,
    user_id: int,
    request: ScriptGenerateRequest,
) -> Script:
    length_guide = {
        "short": "Write a short-form script suitable for YouTube Shorts (45-90 seconds spoken). Keep it punchy and high-energy.",
        "medium": "Write a medium-length script for a 3-6 minute YouTube video.",
        "long": "Write a detailed long-form script for an 8-15 minute YouTube video with clear sections.",
    }
    type_guide = {
        "educational": "Focus on clear explanations, examples, and actionable takeaways. Teach the viewer something valuable.",
        "motivational": "Inspire and energize the viewer. Use powerful language, stories, and calls to action.",
        "technology": "Explain tech concepts clearly, use analogies, stay accurate and up-to-date in tone.",
        "short": "Optimize for vertical short-form: hook in first 3 seconds, fast pacing, strong CTA at end.",
        "long": "Structure with intro, multiple value sections, and strong conclusion.",
        "general": "Create an engaging general-interest video script.",
    }

    prompt = f"""Create a complete YouTube video script.

Topic: {request.topic}
Script type: {request.script_type}
Length: {request.length}
Tone: {request.tone}

{length_guide.get(request.length, length_guide['medium'])}
{type_guide.get(request.script_type, type_guide['general'])}

Requirements:
- Start with a strong hook in the first 1-2 sentences that creates curiosity or emotion.
- Write the full spoken script (what the narrator will say).
- Use short paragraphs and natural spoken language.
- End with a clear call-to-action (subscribe, like, comment, or next video).
- Do NOT include stage directions or [music] tags in the main script body.
"""

    if request.generate_title or request.generate_description or request.generate_hashtags:
        prompt += """
Also generate metadata. Return a JSON object with these exact keys:
{
  "title": "catchy YouTube title under 70 characters",
  "description": "SEO-friendly description 2-4 sentences with call to action",
  "hashtags": ["#tag1", "#tag2", ... up to 8 relevant hashtags],
  "keywords": ["keyword1", "keyword2", ... 5-10 SEO keywords],
  "script": "the full spoken script text here"
}
"""
    else:
        prompt += '\nReturn JSON: {"script": "the full spoken script"}'

    result = await ollama_service.generate_json(prompt, system=SYSTEM_PROMPT, temperature=0.75)

    script_text = result.get("script") or result.get("raw") or str(result)
    title = result.get("title") if request.generate_title else None
    description = result.get("description") if request.generate_description else None
    hashtags = result.get("hashtags", []) if request.generate_hashtags else []
    keywords = result.get("keywords", [])

    if isinstance(hashtags, str):
        hashtags = [h.strip() for h in hashtags.split() if h.strip()]
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    word_count = len(script_text.split())
    duration = estimate_duration(word_count)

    db_script = Script(
        user_id=user_id,
        topic=request.topic,
        title=title or f"{request.topic[:80]}",
        description=description,
        content=script_text,
        script_type=request.script_type,
        hashtags=hashtags,
        keywords=keywords,
        word_count=word_count,
        estimated_duration_seconds=duration,
        model_used=settings.OLLAMA_MODEL,
    )
    db.add(db_script)
    db.add(
        ActivityLog(
            user_id=user_id,
            action="script_generated",
            entity_type="script",
            details={"topic": request.topic, "word_count": word_count},
        )
    )
    db.commit()
    db.refresh(db_script)
    return db_script


async def improve_script(db: Session, script: Script, instruction: str) -> Script:
    prompt = f"""Improve the following YouTube script based on this instruction: {instruction}

Current script:
{script.content}

Return JSON: {{"script": "improved full script", "title": "optional improved title"}}
"""
    result = await ollama_service.generate_json(prompt, system=SYSTEM_PROMPT)
    new_content = result.get("script") or script.content
    if result.get("title"):
        script.title = result["title"]
    script.content = new_content
    script.word_count = len(new_content.split())
    script.estimated_duration_seconds = estimate_duration(script.word_count)
    db.commit()
    db.refresh(script)
    return script
