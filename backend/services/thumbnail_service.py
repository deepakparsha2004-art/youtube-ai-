"""
Thumbnail generation using Pillow.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import uuid
from config import settings


def _get_font(size: int):
    # Try common system fonts; fall back to default
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


async def generate_thumbnail(
    video_id: int,
    title: str,
    is_short: bool = False,
    style: str = "modern",
    background_color: str = None,
) -> str:
    """
    Create a YouTube thumbnail (1280x720 for regular, or 1080x1920 for shorts style).
    Returns path to PNG/JPG.
    """
    if is_short:
        width, height = 1080, 1920
    else:
        width, height = 1280, 720

    # Dark navy / blue glass theme
    if background_color:
        try:
            bg = tuple(int(background_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        except Exception:
            bg = (15, 23, 42)
    else:
        bg = (15, 23, 42)  # slate-900

    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Accent gradient-like bars
    accent = (56, 189, 248)  # sky-400
    accent2 = (99, 102, 241)  # indigo-500
    draw.rectangle([0, 0, width, 12], fill=accent)
    draw.rectangle([0, height - 12, width, height], fill=accent2)

    # Decorative circles (glass effect suggestion)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse([width - 300, -100, width + 100, 300], fill=(56, 189, 248, 40))
    odraw.ellipse([-100, height - 250, 250, height + 50], fill=(99, 102, 241, 35))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Title text
    max_chars = 28 if not is_short else 22
    wrapped = textwrap.fill(title[:90], width=max_chars)
    lines = wrapped.split("\n")[:4]

    font_size = 72 if not is_short else 64
    font = _get_font(font_size)
    line_height = font_size + 16

    total_text_h = len(lines) * line_height
    y_start = (height - total_text_h) // 2 - 20

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        y = y_start + i * line_height
        # Shadow
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    # Small brand label
    brand_font = _get_font(28)
    brand = "AI COMMAND CENTER"
    bbox = draw.textbbox((0, 0), brand, font=brand_font)
    bw = bbox[2] - bbox[0]
    draw.text(((width - bw) // 2, height - 60), brand, font=brand_font, fill=(148, 163, 184))

    filename = f"thumb_{video_id}_{uuid.uuid4().hex[:8]}.png"
    path = settings.THUMBNAILS_DIR / filename
    img.save(path, "PNG", quality=95)
    return str(path)
