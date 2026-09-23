"""
Explain IQ — Video Assembler
============================
Syncs visual slides and images with TTS audio and assembles the final .mp4 video
using MoviePy with crisp 1080p slide transitions and stereo audio.
Compatible with both MoviePy 1.x and 2.x.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Monkey-patch PIL.Image.ANTIALIAS for MoviePy 1.x compatibility with Pillow 10+
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    setattr(PIL.Image, "ANTIALIAS", PIL.Image.Resampling.LANCZOS)

# Import MoviePy with backward-compatibility for 1.x and 2.x
try:
    from moviepy.editor import (
        VideoFileClip,
        ImageClip,
        AudioFileClip,
        CompositeVideoClip,
        concatenate_videoclips,
        vfx,
    )
    MOVIEPY_V2 = False
except ImportError:
    from moviepy import (
        VideoFileClip,
        ImageClip,
        AudioFileClip,
        CompositeVideoClip,
        concatenate_videoclips,
        vfx,
    )
    MOVIEPY_V2 = True

from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS

logger = logging.getLogger(__name__)


@dataclass
class SceneAssets:
    """Holds all file paths and metadata for a single assembled scene."""
    scene_id: int
    visual_path: Path           # .png from Slide/Image or .mp4
    audio_path: Path            # .mp3 from TTS
    audio_duration: float       # seconds
    visual_type: str            # "slide", "image", or legacy "manim"


# ── Scene Clip Synchronization ─────────────────────────────────

def sync_scene_clip(
    visual_path: Path,
    audio_path: Path,
    target_duration: float,
    visual_type: str = "slide",
) -> VideoFileClip:
    """
    Create a synchronized video clip from visual slide + voiceover audio.
    Ensures high-resolution, rock-solid video frames with matching audio track.
    """
    logger.info(
        f"Syncing scene: {visual_path.name} + {audio_path.name} → {target_duration:.1f}s"
    )

    audio = AudioFileClip(str(audio_path))
    target_duration = max(0.5, float(target_duration))
    is_video = str(visual_path).lower().endswith(".mp4")

    if is_video:
        if MOVIEPY_V2:
            video = VideoFileClip(str(visual_path))
            if video.duration < target_duration:
                frozen = video.to_ImageClip(t=max(0, video.duration - 0.1)).with_duration(target_duration - video.duration)
                video = concatenate_videoclips([video, frozen])
            elif video.duration > target_duration:
                video = video.subclipped(0, target_duration)
            video = video.resized((VIDEO_WIDTH, VIDEO_HEIGHT)).with_audio(audio).with_duration(target_duration)
        else:
            video = VideoFileClip(str(visual_path))
            if video.duration < target_duration:
                frozen = video.to_ImageClip(t=max(0, video.duration - 0.1)).set_duration(target_duration - video.duration)
                video = concatenate_videoclips([video, frozen])
            elif video.duration > target_duration:
                video = video.subclip(0, target_duration)
            video = video.resize((VIDEO_WIDTH, VIDEO_HEIGHT)).set_audio(audio).set_duration(target_duration)
    else:
        if MOVIEPY_V2:
            video = (
                ImageClip(str(visual_path))
                .with_duration(target_duration)
                .resized((VIDEO_WIDTH, VIDEO_HEIGHT))
                .with_audio(audio)
            )
        else:
            video = (
                ImageClip(str(visual_path))
                .set_duration(target_duration)
                .resize((VIDEO_WIDTH, VIDEO_HEIGHT))
                .set_audio(audio)
            )

    return video


# ── Final Video Assembly ───────────────────────────────────────

def assemble_final_video(
    scenes: list[SceneAssets],
    output_path: Path,
    crossfade_duration: float = 0.3,
) -> Path:
    """
    Assemble all scene clips into the final educational video.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Assembling {len(scenes)} scenes into final video: {output_path.name}")

    clips = []
    for scene in scenes:
        try:
            clip = sync_scene_clip(
                visual_path=scene.visual_path,
                audio_path=scene.audio_path,
                target_duration=scene.audio_duration,
                visual_type=scene.visual_type,
            )
            clips.append(clip)
            logger.info(f"  Scene {scene.scene_id}: {scene.audio_duration:.1f}s ✓")
        except Exception as e:
            logger.error(f"  Scene {scene.scene_id} sync failed: {e}", exc_info=True)

    if not clips:
        raise RuntimeError("No scenes could be assembled into the final video")

    final = concatenate_videoclips(clips, method="compose")

    logger.info(f"Writing output video: {output_path}")
    final.write_videofile(
        str(output_path),
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None,
        threads=4,
    )

    # Clean up clip resources
    for clip in clips:
        try:
            clip.close()
        except Exception:
            pass
    try:
        final.close()
    except Exception:
        pass

    total_duration = sum(s.audio_duration for s in scenes)
    logger.info(f"Final video successfully generated: {output_path} ({total_duration:.1f}s)")
    return output_path
