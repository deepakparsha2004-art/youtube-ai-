"""
Content research & topic suggestion service (uses Ollama + optional public trends).
"""

from datetime import datetime
import logging
from typing import List
import httpx
from services.ollama_service import ollama_service
from schemas import TopicSuggestion, ResearchResponse

logger = logging.getLogger(__name__)


async def suggest_topics(
    niche: str = "technology",
    count: int = 8,
    style: str = "trending",
) -> ResearchResponse:
    prompt = f"""You are a YouTube content strategist.
Generate {count} high-potential video topic ideas for the niche: "{niche}".
Style preference: {style}.

For each topic provide:
- A catchy, searchable topic title
- Brief reason why it could perform well
- Estimated interest level (High / Medium / Rising)
- 3-5 related keywords

Return JSON:
{{
  "suggestions": [
    {{
      "topic": "...",
      "reason": "...",
      "estimated_interest": "High",
      "keywords": ["k1", "k2"]
    }}
  ]
}}
"""
    try:
        result = await ollama_service.generate_json(
            prompt,
            system="You help creators find viral-friendly, non-clickbait educational and valuable content ideas.",
            temperature=0.8,
        )
    except httpx.HTTPError:
        logger.warning("Topic research unavailable from Ollama; returning fallback ideas", exc_info=True)
        result = {}
    suggestions = []
    for item in result.get("suggestions", []):
        suggestions.append(
            TopicSuggestion(
                topic=item.get("topic", "Untitled"),
                reason=item.get("reason", ""),
                estimated_interest=item.get("estimated_interest", "Medium"),
                keywords=item.get("keywords", []),
            )
        )
    if not suggestions:
        # Minimal fallback
        suggestions = [
            TopicSuggestion(
                topic=f"Emerging {niche} trends to watch",
                reason="Evergreen list format performs well",
                estimated_interest="Medium",
                keywords=[niche, "trends", "innovation"],
            )
        ]
    return ResearchResponse(suggestions=suggestions[:count], generated_at=datetime.utcnow())
