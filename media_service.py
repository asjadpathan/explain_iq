"""
Explain IQ — Media Services
==========================
TTS audio generation via edge-tts and stock image fetching (mock with Pillow).
"""

import asyncio
import logging
import random
import textwrap
from pathlib import Path

import edge_tts
from mutagen.mp3 import MP3
from PIL import Image, ImageDraw, ImageFont

from config import TTS_VOICE, VIDEO_WIDTH, VIDEO_HEIGHT

logger = logging.getLogger(__name__)


# ── TTS Audio Generation ──────────────────────────────────────

async def generate_tts(
    text: str,
    output_path: Path,
    voice: str = TTS_VOICE,
) -> tuple[Path, float]:
    """
    Generate TTS audio for the given text using Microsoft Edge neural voices.

    Args:
        text: The narration text to synthesize.
        output_path: Where to save the .mp3 file.
        voice: Edge TTS voice name (e.g., "en-US-AriaNeural").

    Returns:
        Tuple of (path to saved .mp3, duration in seconds).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating TTS: {len(text)} chars → {output_path.name}")

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))

    # Get accurate duration via mutagen
    audio = MP3(str(output_path))
    duration = audio.info.length

    logger.info(f"TTS generated: {output_path.name} ({duration:.1f}s)")
    return output_path, duration


# ── Stock Image Service ────────────────────────────────────────
# TODO: Replace with Unsplash/Pexels API call for real stock photos.
#       For now, generates professional gradient placeholders.

# Curated color palettes for visually appealing gradients
COLOR_PALETTES = [
    ("#667eea", "#764ba2"),  # Purple gradient
    ("#f093fb", "#f5576c"),  # Pink gradient
    ("#4facfe", "#00f2fe"),  # Blue-cyan gradient
    ("#43e97b", "#38f9d7"),  # Green-teal gradient
    ("#fa709a", "#fee140"),  # Pink-yellow gradient
    ("#a18cd1", "#fbc2eb"),  # Lavender gradient
    ("#ffecd2", "#fcb69f"),  # Peach gradient
    ("#89f7fe", "#66a6ff"),  # Cyan-blue gradient
    ("#fddb92", "#d1fdff"),  # Yellow-light gradient
    ("#c1dfc4", "#deecdd"),  # Soft green gradient
]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


async def fetch_stock_image(
    search_query: str,
    output_path: Path,
    alt_text: str = "",
) -> Path:
    """
    Fetch (or generate) a stock image for the given search query.

    Currently generates a gradient placeholder with text overlay.
    TODO: Replace with Unsplash/Pexels API integration.

    Args:
        search_query: What kind of image to find (used as overlay text).
        output_path: Where to save the image.
        alt_text: Accessible description (used in subtitle).

    Returns:
        Path to the saved image file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate in a thread to avoid blocking the event loop
    await asyncio.to_thread(
        _create_gradient_image,
        search_query,
        alt_text,
        output_path,
    )

    logger.info(f"Stock image generated: {output_path.name} (query: {search_query})")
    return output_path


def _create_gradient_image(
    search_query: str,
    alt_text: str,
    output_path: Path,
) -> None:
    """Create a visually appealing gradient image with text overlay."""
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)

    # Pick a random color palette
    color1_hex, color2_hex = random.choice(COLOR_PALETTES)
    color1 = _hex_to_rgb(color1_hex)
    color2 = _hex_to_rgb(color2_hex)

    # Draw smooth vertical/diagonal gradient quickly
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b))

    # Add semi-transparent overlay for text readability
    overlay = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 100))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        font_large = ImageFont.truetype("arial.ttf", 52)
        font_small = ImageFont.truetype("arial.ttf", 28)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Main text (search query)
    query_wrapped = textwrap.fill(search_query, width=30)
    bbox = draw.textbbox((0, 0), query_wrapped, font=font_large)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (VIDEO_WIDTH - text_w) // 2
    y = (VIDEO_HEIGHT - text_h) // 2 - 20

    # Text shadow for depth
    draw.text((x + 2, y + 2), query_wrapped, fill=(0, 0, 0), font=font_large)
    draw.text((x, y), query_wrapped, fill="white", font=font_large)

    # Alt text as subtitle
    if alt_text:
        alt_wrapped = textwrap.fill(alt_text, width=50)
        bbox_a = draw.textbbox((0, 0), alt_wrapped, font=font_small)
        aw = bbox_a[2] - bbox_a[0]
        ax = (VIDEO_WIDTH - aw) // 2
        ay = y + text_h + 40
        draw.text((ax + 1, ay + 1), alt_wrapped, fill=(0, 0, 0), font=font_small)
        draw.text((ax, ay), alt_wrapped, fill=(220, 220, 220), font=font_small)

    # Decorative corner accents
    accent_color = "white"
    accent_len = 60
    accent_width = 3
    # Top-left
    draw.line([(40, 40), (40 + accent_len, 40)], fill=accent_color, width=accent_width)
    draw.line([(40, 40), (40, 40 + accent_len)], fill=accent_color, width=accent_width)
    # Top-right
    draw.line([(VIDEO_WIDTH - 40, 40), (VIDEO_WIDTH - 40 - accent_len, 40)], fill=accent_color, width=accent_width)
    draw.line([(VIDEO_WIDTH - 40, 40), (VIDEO_WIDTH - 40, 40 + accent_len)], fill=accent_color, width=accent_width)
    # Bottom-left
    draw.line([(40, VIDEO_HEIGHT - 40), (40 + accent_len, VIDEO_HEIGHT - 40)], fill=accent_color, width=accent_width)
    draw.line([(40, VIDEO_HEIGHT - 40), (40, VIDEO_HEIGHT - 40 - accent_len)], fill=accent_color, width=accent_width)
    # Bottom-right
    draw.line(
        [(VIDEO_WIDTH - 40, VIDEO_HEIGHT - 40), (VIDEO_WIDTH - 40 - accent_len, VIDEO_HEIGHT - 40)],
        fill=accent_color,
        width=accent_width,
    )
    draw.line(
        [(VIDEO_WIDTH - 40, VIDEO_HEIGHT - 40), (VIDEO_WIDTH - 40, VIDEO_HEIGHT - 40 - accent_len)],
        fill=accent_color,
        width=accent_width,
    )

    img.save(output_path, "PNG")
