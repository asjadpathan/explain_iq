"""
Explain IQ — Slide Generation Service
=====================================
Generates high-resolution (1920x1080) educational graphic slides
using Pillow with modern typography, gradients, glassmorphism cards,
and accent badges. Replaces heavy Manim dependencies with fast,
reliable, and beautiful native graphics.
"""

import logging
import textwrap
from pathlib import Path
from typing import Optional, Union

from PIL import Image, ImageDraw, ImageFont

from config import VIDEO_WIDTH, VIDEO_HEIGHT

logger = logging.getLogger(__name__)

# ── Design Tokens & Color Palettes ────────────────────────────

BG_DARK_THEMES = [
    # (top_color, bottom_color, accent_color)
    ((11, 15, 25), (20, 27, 45), "#38BDF8"),      # Deep obsidian & slate navy (cyan accent)
    ((15, 23, 42), (30, 41, 59), "#818CF8"),      # Slate dark (indigo accent)
    ((10, 15, 30), (24, 18, 43), "#A78BFA"),      # Midnight violet
    ((13, 27, 30), (19, 42, 45), "#34D399"),      # Deep forest emerald
    ((26, 18, 26), (41, 23, 38), "#F472B6"),      # Rose dark
]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex string (e.g., '#38BDF8') to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (56, 189, 248)


def _get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Load standard system font with graceful fallback."""
    font_candidates = [
        "segoeui.ttf", "segoeuib.ttf" if bold else "segoeui.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "arial.ttf",
        "calibri.ttf",
    ]
    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _draw_gradient_background(
    img: Image.Image,
    top_color: tuple[int, int, int] = (11, 15, 25),
    bottom_color: tuple[int, int, int] = (20, 27, 45),
) -> None:
    """Draw a smooth vertical gradient on the image."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for y in range(h):
        ratio = y / h
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _draw_accent_decorations(
    draw: ImageDraw.Draw,
    accent_rgb: tuple[int, int, int],
    badge_text: str = "EXPLAIN IQ",
) -> None:
    """Draw top header badge and subtle framing corner accents."""
    # Top badge pill
    font_badge = _get_font(20, bold=True)
    badge_w = len(badge_text) * 11 + 24
    badge_x = (VIDEO_WIDTH - badge_w) // 2
    badge_y = 48
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + 36],
        radius=18,
        fill=(accent_rgb[0] // 5, accent_rgb[1] // 5, accent_rgb[2] // 5),
        outline=accent_rgb,
        width=2,
    )
    draw.text(
        (badge_x + 12, badge_y + 7),
        badge_text,
        fill=accent_rgb,
        font=font_badge,
    )

    # Subtle corner accents
    corner_len = 40
    corner_w = 2
    margin = 32
    color = (80, 95, 120)
    # Top-left
    draw.line([(margin, margin), (margin + corner_len, margin)], fill=color, width=corner_w)
    draw.line([(margin, margin), (margin, margin + corner_len)], fill=color, width=corner_w)
    # Top-right
    draw.line([(VIDEO_WIDTH - margin, margin), (VIDEO_WIDTH - margin - corner_len, margin)], fill=color, width=corner_w)
    draw.line([(VIDEO_WIDTH - margin, margin), (VIDEO_WIDTH - margin, margin + corner_len)], fill=color, width=corner_w)
    # Bottom-left
    draw.line([(margin, VIDEO_HEIGHT - margin), (margin + corner_len, VIDEO_HEIGHT - margin)], fill=color, width=corner_w)
    draw.line([(margin, VIDEO_HEIGHT - margin), (margin, VIDEO_HEIGHT - margin - corner_len)], fill=color, width=corner_w)
    # Bottom-right
    draw.line([(VIDEO_WIDTH - margin, VIDEO_HEIGHT - margin), (VIDEO_WIDTH - margin - corner_len, VIDEO_HEIGHT - margin)], fill=color, width=corner_w)
    draw.line([(VIDEO_WIDTH - margin, VIDEO_HEIGHT - margin), (VIDEO_WIDTH - margin, VIDEO_HEIGHT - margin - corner_len)], fill=color, width=corner_w)


# ── Template 1: Title Card ────────────────────────────────────

def render_title_card(
    title: str,
    subtitle: Optional[str] = None,
    highlight_color: str = "#38BDF8",
    output_path: Optional[Path] = None,
) -> Image.Image:
    """Render a title card with prominent typography and modern backdrop."""
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT))
    _draw_gradient_background(img, (11, 17, 32), (23, 27, 54))
    draw = ImageDraw.Draw(img)
    accent_rgb = _hex_to_rgb(highlight_color)

    _draw_accent_decorations(draw, accent_rgb, badge_text="EDUCATIONAL EXPLAINER")

    # Center card container
    card_x1, card_y1 = 160, 180
    card_x2, card_y2 = VIDEO_WIDTH - 160, VIDEO_HEIGHT - 180
    draw.rounded_rectangle(
        [card_x1, card_y1, card_x2, card_y2],
        radius=24,
        fill=(17, 24, 39),
        outline=(55, 65, 81),
        width=2,
    )

    # Accent glow top bar on card
    draw.rounded_rectangle(
        [card_x1 + 40, card_y1 + 4, card_x2 - 40, card_y1 + 10],
        radius=3,
        fill=accent_rgb,
    )

    # Fonts
    font_title = _get_font(60, bold=True)
    font_sub = _get_font(32)

    # Title text wrapping
    title_wrapped = textwrap.fill(title, width=32)
    bbox = draw.textbbox((0, 0), title_wrapped, font=font_title, align="center")
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    tx = (VIDEO_WIDTH - tw) // 2
    ty = (VIDEO_HEIGHT - th) // 2 - (40 if subtitle else 0)

    # Title shadow + text
    draw.text((tx + 3, ty + 3), title_wrapped, fill=(0, 0, 0), font=font_title, align="center")
    draw.text((tx, ty), title_wrapped, fill=(255, 255, 255), font=font_title, align="center")

    # Accent divider
    line_y = ty + th + 32
    draw.line(
        [(VIDEO_WIDTH // 2 - 140, line_y), (VIDEO_WIDTH // 2 + 140, line_y)],
        fill=accent_rgb,
        width=4,
    )

    # Subtitle
    if subtitle:
        sub_wrapped = textwrap.fill(subtitle, width=54)
        sbox = draw.textbbox((0, 0), sub_wrapped, font=font_sub, align="center")
        sw = sbox[2] - sbox[0]
        sx = (VIDEO_WIDTH - sw) // 2
        sy = line_y + 28
        draw.text((sx, sy), sub_wrapped, fill=(203, 213, 225), font=font_sub, align="center")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
    return img


# ── Template 2: Bullet Points ─────────────────────────────────

def render_bullet_slide(
    title: str,
    bullet_points: list[str],
    highlight_color: str = "#38BDF8",
    output_path: Optional[Path] = None,
) -> Image.Image:
    """Render a structured bullet list card."""
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT))
    _draw_gradient_background(img, (13, 19, 33), (22, 30, 49))
    draw = ImageDraw.Draw(img)
    accent_rgb = _hex_to_rgb(highlight_color)

    _draw_accent_decorations(draw, accent_rgb, badge_text="KEY CONCEPTS")

    # Slide Title
    font_head = _get_font(46, bold=True)
    head_wrapped = textwrap.fill(title, width=44)
    draw.text((120, 110), head_wrapped, fill=(255, 255, 255), font=font_head)

    # Underline under title
    bbox = draw.textbbox((120, 110), head_wrapped, font=font_head)
    line_y = bbox[3] + 16
    draw.line([(120, line_y), (360, line_y)], fill=accent_rgb, width=4)

    # Bullets container card
    card_x1, card_y1 = 120, line_y + 36
    card_x2, card_y2 = VIDEO_WIDTH - 120, VIDEO_HEIGHT - 90
    draw.rounded_rectangle(
        [card_x1, card_y1, card_x2, card_y2],
        radius=20,
        fill=(17, 24, 39),
        outline=(55, 65, 81),
        width=2,
    )

    bullets = (bullet_points or [])[:4]  # Max 4 items for readability
    if not bullets:
        bullets = ["Core principle overview", "Detailed application", "Key takeaway"]

    font_bullet = _get_font(30)
    font_num = _get_font(22, bold=True)

    available_h = card_y2 - card_y1 - 60
    item_gap = available_h // max(len(bullets), 1)

    for i, bullet in enumerate(bullets):
        curr_y = card_y1 + 35 + (i * item_gap)

        # Numbered circle badge
        badge_r = 22
        bx, by = card_x1 + 55, curr_y + 16
        draw.ellipse(
            [bx - badge_r, by - badge_r, bx + badge_r, by + badge_r],
            fill=(accent_rgb[0] // 4, accent_rgb[1] // 4, accent_rgb[2] // 4),
            outline=accent_rgb,
            width=2,
        )
        num_str = f"{i + 1:02d}"
        nbox = draw.textbbox((0, 0), num_str, font=font_num)
        nw, nh = nbox[2] - nbox[0], nbox[3] - nbox[1]
        draw.text((bx - nw // 2, by - nh // 2 - 2), num_str, fill=accent_rgb, font=font_num)

        # Bullet text
        b_wrapped = textwrap.fill(bullet, width=64)
        draw.text((card_x1 + 105, curr_y), b_wrapped, fill=(241, 245, 249), font=font_bullet)

        # Subtle separator line (except last)
        if i < len(bullets) - 1:
            sep_y = curr_y + item_gap - 10
            draw.line(
                [(card_x1 + 40, sep_y), (card_x2 - 40, sep_y)],
                fill=(31, 41, 55),
                width=1,
            )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
    return img


# ── Template 3: Concept / Formula Card ────────────────────────

def render_concept_card(
    title: str,
    key_text: str,
    subtitle: Optional[str] = None,
    highlight_color: str = "#F59E0B",
    output_path: Optional[Path] = None,
) -> Image.Image:
    """Render a highlighted focus card for equations, laws, or definitions."""
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT))
    _draw_gradient_background(img, (14, 18, 29), (28, 23, 36))
    draw = ImageDraw.Draw(img)
    accent_rgb = _hex_to_rgb(highlight_color)

    _draw_accent_decorations(draw, accent_rgb, badge_text="CORE PRINCIPLE")

    # Header title
    font_title = _get_font(44, bold=True)
    title_wrapped = textwrap.fill(title, width=42)
    tbox = draw.textbbox((0, 0), title_wrapped, font=font_title, align="center")
    tw = tbox[2] - tbox[0]
    draw.text(((VIDEO_WIDTH - tw) // 2, 120), title_wrapped, fill=(255, 255, 255), font=font_title, align="center")

    # Center callout card
    card_x1, card_y1 = 180, 240
    card_x2, card_y2 = VIDEO_WIDTH - 180, VIDEO_HEIGHT - 180
    draw.rounded_rectangle(
        [card_x1, card_y1, card_x2, card_y2],
        radius=24,
        fill=(19, 24, 38),
        outline=accent_rgb,
        width=3,
    )

    # Highlighted key text (equation, law, rule)
    font_key = _get_font(52, bold=True)
    key_wrapped = textwrap.fill(key_text, width=36)
    kbox = draw.textbbox((0, 0), key_wrapped, font=font_key, align="center")
    kw, kh = kbox[2] - kbox[0], kbox[3] - kbox[1]
    kx = (VIDEO_WIDTH - kw) // 2
    ky = card_y1 + (card_y2 - card_y1 - kh) // 2 - (30 if subtitle else 0)

    # Shadow + glowing colored key text
    draw.text((kx + 2, ky + 2), key_wrapped, fill=(0, 0, 0), font=font_key, align="center")
    draw.text((kx, ky), key_wrapped, fill=accent_rgb, font=font_key, align="center")

    # Subtitle / explanation
    if subtitle:
        font_sub = _get_font(28)
        sub_wrapped = textwrap.fill(subtitle, width=55)
        sbox = draw.textbbox((0, 0), sub_wrapped, font=font_sub, align="center")
        sw = sbox[2] - sbox[0]
        sx = (VIDEO_WIDTH - sw) // 2
        sy = ky + kh + 40
        draw.text((sx, sy), sub_wrapped, fill=(203, 213, 225), font=font_sub, align="center")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
    return img


# ── Unified Slide Dispatcher ──────────────────────────────────

def render_slide(
    template_name: str,
    config_data: dict,
    output_dir: Path,
    scene_id: int,
) -> Path:
    """
    Render an educational slide image based on template name and parameters.
    Replaces render_manim_scene with clean, instant Pillow rendering.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"scene_{scene_id}_slide.png"

    title = config_data.get("title", f"Scene {scene_id}")
    color = config_data.get("highlight_color", "#38BDF8")
    subtitle = config_data.get("subtitle", "")
    bullets = config_data.get("bullet_points", [])
    key_text = config_data.get("equation") or config_data.get("key_text") or title

    logger.info(f"Rendering slide scene {scene_id}: template={template_name}, title='{title}'")

    if template_name in ("title_card", "intro", "outro"):
        render_title_card(
            title=title,
            subtitle=subtitle or (bullets[0] if bullets else ""),
            highlight_color=color,
            output_path=output_path,
        )
    elif template_name in ("text_bullet", "bullets", "summary"):
        render_bullet_slide(
            title=title,
            bullet_points=bullets or [key_text],
            highlight_color=color,
            output_path=output_path,
        )
    elif template_name in ("equation", "concept_card", "callout"):
        render_concept_card(
            title=title,
            key_text=key_text,
            subtitle=subtitle,
            highlight_color=color,
            output_path=output_path,
        )
    else:
        # Fallback to general bullet slide
        render_bullet_slide(
            title=title,
            bullet_points=bullets or [key_text],
            highlight_color=color,
            output_path=output_path,
        )

    return output_path
