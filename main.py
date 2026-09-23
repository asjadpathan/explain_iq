"""
Explain IQ — FastAPI Video Generation Microservice
==================================================
Orchestrates LLM storyboarding, TTS audio, visual slide rendering,
and MoviePy assembly to produce educational explainer videos.
"""

import asyncio
import logging
import shutil
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config import OUTPUT_DIR, TEMP_DIR
from llm_service import generate_storyboard
from slide_service import render_slide
from media_service import generate_tts, fetch_stock_image
from assembler import SceneAssets, assemble_final_video

# ── Logging Setup ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-18s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("explain_iq")

# ── Job Status Management ─────────────────────────────────────

class JobStage(str, Enum):
    QUEUED = "queued"
    STORYBOARDING = "storyboarding"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_VISUALS = "generating_visuals"
    ASSEMBLING = "assembling"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(BaseModel):
    job_id: str
    status: JobStage = JobStage.QUEUED
    progress_pct: int = 0
    current_stage: str = "Waiting in queue"
    error: Optional[str] = None
    video_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# In-memory job store
jobs: dict[str, JobStatus] = {}


def update_job(job_id: str, **kwargs) -> None:
    """Update job status fields atomically."""
    if job_id in jobs:
        for key, value in kwargs.items():
            setattr(jobs[job_id], key, value)
        jobs[job_id].updated_at = datetime.now(timezone.utc)


# ── Pydantic Request/Response Models ──────────────────────────

class GenerateRequest(BaseModel):
    concept: str = Field(
        ...,
        description="The educational concept to create a video about",
        min_length=3,
        max_length=500,
        examples=["Newton's Laws of Motion", "Photosynthesis", "The Water Cycle"],
    )
    target_audience: str = Field(
        default="high school students",
        description="Who the video is aimed at",
        examples=["high school students", "college freshmen", "middle school students"],
    )


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStage
    progress_pct: int
    current_stage: str
    error: Optional[str]
    video_url: Optional[str]
    created_at: datetime
    updated_at: datetime


# ── FastAPI Application ───────────────────────────────────────

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎬 Explain IQ Video Generation Service starting up")
    logger.info(f"   Output directory: {OUTPUT_DIR}")
    logger.info(f"   Temp directory: {TEMP_DIR}")
    yield
    logger.info("🛑 Explain IQ shutting down")


app = FastAPI(
    title="Explain IQ Video Generation API",
    description=(
        "Generate short educational explainer videos from a concept description. "
        "Uses Gemini for storyboarding, native slide/image engine for visuals, "
        "edge-tts for voiceover, and MoviePy for assembly."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ──────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "explain_iq",
        "active_jobs": len([j for j in jobs.values() if j.status not in (JobStage.COMPLETED, JobStage.FAILED)]),
        "total_jobs": len(jobs),
    }


@app.post("/generate", status_code=202, response_model=GenerateResponse)
async def generate_video(request: GenerateRequest):
    """
    Start generating an educational video for the given concept.
    Returns immediately with a job_id for status polling.
    """
    job_id = str(uuid.uuid4())

    # Initialize job status
    jobs[job_id] = JobStatus(job_id=job_id)

    # Launch pipeline as background task
    asyncio.create_task(run_pipeline(job_id, request.concept, request.target_audience))

    logger.info(f"Job {job_id[:8]} created for concept: {request.concept}")

    return GenerateResponse(
        job_id=job_id,
        status="queued",
        message=f"Video generation started. Poll /status/{job_id} for progress.",
    )


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the current status of a video generation job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress_pct=job.progress_pct,
        current_stage=job.current_stage,
        error=job.error,
        video_url=job.video_url,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@app.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download the completed video file."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = jobs[job_id]

    if job.status == JobStage.FAILED:
        raise HTTPException(status_code=500, detail=f"Job failed: {job.error}")

    if job.status != JobStage.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Video not ready. Current status: {job.status.value} ({job.progress_pct}%)",
        )

    video_path = OUTPUT_DIR / f"{job_id}.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"explain_iq_{job_id[:8]}.mp4",
    )


# ── Background Pipeline ───────────────────────────────────────

async def run_pipeline(job_id: str, concept: str, target_audience: str) -> None:
    """
    Full video generation pipeline:
    1. Generate storyboard via Gemini LLM
    2. Generate TTS audio for each scene
    3. Generate visual slides and illustrative images
    4. Assemble final video with MoviePy (Ken Burns + crossfade)
    """
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ── Stage 1: Storyboarding ────────────────────────────
        update_job(
            job_id,
            status=JobStage.STORYBOARDING,
            progress_pct=5,
            current_stage="Generating storyboard with Gemini...",
        )

        storyboard = await generate_storyboard(concept, target_audience)
        num_scenes = len(storyboard.scenes)

        logger.info(f"[{job_id[:8]}] Storyboard: '{storyboard.title}' — {num_scenes} scenes")

        update_job(
            job_id,
            progress_pct=15,
            current_stage=f"Storyboard ready: {num_scenes} scenes",
        )

        # ── Stage 2: TTS Audio Generation ─────────────────────
        update_job(
            job_id,
            status=JobStage.GENERATING_AUDIO,
            progress_pct=20,
            current_stage="Generating voiceover audio...",
        )

        audio_dir = job_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        scene_durations: dict[int, float] = {}

        for i, scene in enumerate(storyboard.scenes):
            audio_path = audio_dir / f"scene_{scene.scene_id}.mp3"
            _, duration = await generate_tts(scene.narration_text, audio_path)
            scene_durations[scene.scene_id] = duration

            progress = 20 + int((i + 1) / num_scenes * 20)  # 20% → 40%
            update_job(
                job_id,
                progress_pct=progress,
                current_stage=f"Audio: scene {i + 1}/{num_scenes} ({duration:.1f}s)",
            )

        # ── Stage 3: Visual Generation ────────────────────────
        update_job(
            job_id,
            status=JobStage.GENERATING_VISUALS,
            progress_pct=40,
            current_stage="Generating visual assets...",
        )

        visuals_dir = job_dir / "visuals"
        visuals_dir.mkdir(exist_ok=True)
        images_dir = job_dir / "images"
        images_dir.mkdir(exist_ok=True)

        scene_assets: list[SceneAssets] = []

        for i, scene in enumerate(storyboard.scenes):
            audio_path = audio_dir / f"scene_{scene.scene_id}.mp3"
            duration = scene_durations[scene.scene_id]

            if scene.visual_type in ("slide", "manim"):
                meta = scene.slide_metadata or scene.manim_metadata
                template = meta.template if meta else ("title_card" if i == 0 else "text_bullet")
                title = meta.title if meta else storyboard.title
                subtitle = meta.subtitle if meta else None
                bullets = meta.bullet_points if meta else []
                key_text = meta.key_text if (meta and hasattr(meta, "key_text")) else None
                color = meta.highlight_color if meta else "#38BDF8"

                config_data = {
                    "title": title,
                    "subtitle": subtitle,
                    "bullet_points": bullets,
                    "key_text": key_text,
                    "highlight_color": color,
                    "duration": duration,
                }

                visual_path = await asyncio.to_thread(
                    render_slide,
                    template,
                    config_data,
                    visuals_dir,
                    scene.scene_id,
                )
            elif scene.visual_type == "image" and scene.image_metadata:
                image_path = images_dir / f"scene_{scene.scene_id}.png"
                visual_path = await fetch_stock_image(
                    search_query=scene.image_metadata.search_query,
                    output_path=image_path,
                    alt_text=scene.image_metadata.alt_text,
                )
            else:
                image_path = images_dir / f"scene_{scene.scene_id}.png"
                visual_path = await fetch_stock_image(
                    search_query=concept,
                    output_path=image_path,
                    alt_text=f"Scene {scene.scene_id}",
                )

            scene_assets.append(SceneAssets(
                scene_id=scene.scene_id,
                visual_path=Path(visual_path),
                audio_path=audio_path,
                audio_duration=duration,
                visual_type=scene.visual_type,
            ))

            progress = 40 + int((i + 1) / num_scenes * 35)  # 40% → 75%
            update_job(
                job_id,
                progress_pct=progress,
                current_stage=f"Visuals: scene {i + 1}/{num_scenes} ({scene.visual_type})",
            )

        # ── Stage 4: Final Assembly ───────────────────────────
        update_job(
            job_id,
            status=JobStage.ASSEMBLING,
            progress_pct=80,
            current_stage="Assembling final video with MoviePy...",
        )

        output_path = OUTPUT_DIR / f"{job_id}.mp4"

        await asyncio.to_thread(
            assemble_final_video,
            scene_assets,
            output_path,
        )

        # ── Done ──────────────────────────────────────────────
        update_job(
            job_id,
            status=JobStage.COMPLETED,
            progress_pct=100,
            current_stage="Video generation complete!",
            video_url=f"/download/{job_id}",
        )

        total_duration = sum(scene_durations.values())
        logger.info(
            f"[{job_id[:8]}] ✅ Video complete: {output_path} "
            f"({total_duration:.1f}s, {num_scenes} scenes)"
        )

        # Clean up temp files
        try:
            shutil.rmtree(job_dir)
            logger.info(f"[{job_id[:8]}] Temp files cleaned up")
        except Exception as e:
            logger.warning(f"[{job_id[:8]}] Cleanup warning: {e}")

    except Exception as e:
        logger.error(f"[{job_id[:8]}] ❌ Pipeline failed: {e}", exc_info=True)
        update_job(
            job_id,
            status=JobStage.FAILED,
            current_stage="Pipeline failed",
            error=str(e),
        )


# ── Run directly with: python main.py ─────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )

