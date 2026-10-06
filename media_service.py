"""
Explain IQ — Media Services
==========================
TTS audio generation via edge-tts (with word-level subtitle capture)
and real stock image fetching from Pexels API and Wikimedia Commons API.
No AI image generation — fetches real, high-resolution photography and graphics.
"""

import asyncio
import json
import logging
import random
import textwrap
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import edge_tts
from mutagen.mp3 import MP3
from PIL import Image, ImageDraw, ImageFont

from config import TTS_VOICE, VIDEO_WIDTH, VIDEO_HEIGHT, PEXELS_API_KEY

logger = logging.getLogger(__name__)

USER_AGENT = "ExplainIQ/1.0 (Educational Explainer Video Microservice; contact@explainiq.local)"


# ── TTS Audio & Subtitle Generation ────────────────────────────

async def generate_tts(
    text: str,
    output_path: Path,
    voice: str = TTS_VOICE,
    srt_output_path: Optional[Path] = None,
) -> Tuple[Path, float]:
    """
    Generate TTS audio for narration text using Microsoft Edge neural voices.
    Also extracts word boundary timestamps for .srt subtitle generation.

    Returns:
        Tuple of (path to saved .mp3, duration in seconds).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating TTS: {len(text)} chars → {output_path.name}")

    communicate = edge_tts.Communicate(text, voice)
    sub_maker = getattr(edge_tts, "SubMaker", None)() if hasattr(edge_tts, "SubMaker") else None

    # Stream audio data and capture word boundaries
    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary" and sub_maker is not None:
                sub_maker.feed(chunk)

    # Save scene SRT if requested and available
    if srt_output_path and sub_maker is not None:
        try:
            srt_content = sub_maker.get_srt()
            if srt_content:
                srt_output_path.parent.mkdir(parents=True, exist_ok=True)
                srt_output_path.write_text(srt_content, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not generate scene SRT: {e}")

    # Inspect exact duration with mutagen
    audio = MP3(str(output_path))
    duration = float(audio.info.length)

    logger.info(f"TTS generated: {output_path.name} ({duration:.1f}s)")
    return output_path, duration


# ── Real Stock Image Fetcher ───────────────────────────────────

def _fetch_from_pexels(query: str, api_key: str) -> Optional[bytes]:
    """Search and download a high-res landscape image from Pexels."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.pexels.com/v1/search?query={encoded_query}&per_page=3&orientation=landscape"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": api_key,
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            photos = data.get("photos", [])
            if photos:
                # Prefer large2x (high quality 1080p+), fallback to large or original
                img_url = photos[0].get("src", {}).get("large2x") or photos[0].get("src", {}).get("large")
                if img_url:
                    img_req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT})
                    with urllib.request.urlopen(img_req, timeout=15) as img_resp:
                        return img_resp.read()
    except Exception as e:
        logger.warning(f"Pexels fetch failed for '{query}': {e}")
    return None


def _fetch_from_wikimedia(query: str) -> Optional[bytes]:
    """
    Search and download a free high-resolution educational image from Wikimedia Commons.
    Requires no API key and works globally.
    """
    encoded_query = urllib.parse.quote(query)
    search_url = (
        "https://commons.wikimedia.org/w/api.php?"
        f"action=query&generator=search&gsrsearch={encoded_query}&gsrlimit=6"
        "&prop=imageinfo&iiprop=url|mime|size&format=json"
    )
    req = urllib.request.Request(search_url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})

            candidate_urls = []
            for page in pages.values():
                imageinfo = page.get("imageinfo", [])
                if not imageinfo:
                    continue
                info = imageinfo[0]
                mime = info.get("mime", "")
                width = info.get("width", 0)
                # Filter for raster photos of decent resolution
                if mime in ("image/jpeg", "image/png", "image/webp") and width >= 800:
                    candidate_urls.append(info.get("url"))

            for img_url in candidate_urls[:2]:
                if not img_url:
                    continue
                img_req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(img_req, timeout=15) as img_resp:
                    return img_resp.read()
    except Exception as e:
        logger.warning(f"Wikimedia fetch failed for '{query}': {e}")
    return None


def _process_and_save_image(
    raw_data: bytes,
    output_path: Path,
    alt_text: str = "",
    target_width: int = VIDEO_WIDTH,
    target_height: int = VIDEO_HEIGHT,
) -> None:
    """Center-crop and resize downloaded image to 1920x1080 canvas."""
    from io import BytesIO
    with Image.open(BytesIO(raw_data)) as img:
        img = img.convert("RGB")
        src_w, src_h = img.size

        # Calculate aspect ratios to center-crop without distortion
        target_aspect = target_width / target_height
        src_aspect = src_w / src_h

        if src_aspect > target_aspect:
            # Source is wider: crop sides
            new_w = int(src_h * target_aspect)
            offset = (src_w - new_w) // 2
            crop_box = (offset, 0, offset + new_w, src_h)
        else:
            # Source is taller: crop top/bottom
            new_h = int(src_w / target_aspect)
            offset = (src_h - new_h) // 2
            crop_box = (0, offset, src_w, offset + new_h)

        cropped = img.crop(crop_box).resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Subtle bottom vignette and caption for readability
        if alt_text:
            overlay = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            # Bottom gradient bar
            bar_height = 140
            for y in range(target_height - bar_height, target_height):
                alpha = int(180 * (y - (target_height - bar_height)) / bar_height)
                odraw.line([(0, y), (target_width, y)], fill=(0, 0, 0, alpha))

            # Caption text
            try:
                caption_font = ImageFont.truetype("segoeui.ttf", 26)
            except Exception:
                caption_font = ImageFont.load_default()

            caption = textwrap.fill(alt_text, width=80)
            odraw.text((60, target_height - 90), caption, fill=(240, 240, 240, 230), font=caption_font)

            cropped = Image.alpha_composite(cropped.convert("RGBA"), overlay).convert("RGB")

        cropped.save(output_path, "PNG")


def _generate_fallback_graphic(
    search_query: str,
    alt_text: str,
    output_path: Path,
) -> None:
    """Generate high-contrast graphic card if all network sources are unavailable."""
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Accent decorative lines
    draw.rounded_rectangle([120, 100, VIDEO_WIDTH - 120, VIDEO_HEIGHT - 100], radius=24, outline=(56, 189, 248), width=3)

    try:
        font_main = ImageFont.truetype("segoeuib.ttf", 52)
        font_sub = ImageFont.truetype("segoeui.ttf", 28)
    except Exception:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    wrapped_q = textwrap.fill(search_query, width=36)
    bbox = draw.textbbox((0, 0), wrapped_q, font=font_main)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((VIDEO_WIDTH - w) // 2, (VIDEO_HEIGHT - h) // 2 - 30), wrapped_q, fill=(255, 255, 255), font=font_main, align="center")

    if alt_text:
        wrapped_alt = textwrap.fill(alt_text, width=60)
        abox = draw.textbbox((0, 0), wrapped_alt, font=font_sub)
        aw = abox[2] - abox[0]
        draw.text(((VIDEO_WIDTH - aw) // 2, (VIDEO_HEIGHT - h) // 2 + h + 30), wrapped_alt, fill=(148, 163, 184), font=font_sub, align="center")

    img.save(output_path, "PNG")


async def fetch_stock_image(
    search_query: str,
    output_path: Path,
    alt_text: str = "",
) -> Path:
    """
    Fetch a real stock image matching the search query.
    1. Tries Pexels API if PEXELS_API_KEY is configured.
    2. Falls back to Wikimedia Commons API (no key required).
    3. Falls back to styled graphic card if network fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Fetching real stock image for: '{search_query}'")

    raw_data: Optional[bytes] = None

    # Step 1: Try Pexels if API key is provided
    if PEXELS_API_KEY:
        raw_data = await asyncio.to_thread(_fetch_from_pexels, search_query, PEXELS_API_KEY)

    # Step 2: Try Wikimedia Commons if no image yet
    if not raw_data:
        raw_data = await asyncio.to_thread(_fetch_from_wikimedia, search_query)

    # Step 3: Process downloaded image or create graceful fallback
    if raw_data:
        try:
            await asyncio.to_thread(_process_and_save_image, raw_data, output_path, alt_text)
            logger.info(f"Real stock image saved: {output_path.name}")
            return output_path
        except Exception as e:
            logger.warning(f"Error processing image data: {e}")

    # Fallback graphic
    logger.info(f"Using fallback graphic for '{search_query}'")
    await asyncio.to_thread(_generate_fallback_graphic, search_query, alt_text, output_path)
    return output_path
