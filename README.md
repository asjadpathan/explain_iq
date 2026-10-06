<div align="center">

# 🎬 Explain IQ
### *Autonomous AI Educational Video Generation Microservice*

**Transform any educational topic into a studio-grade 1080p explainer video in minutes.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-Flash--Lite-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_Mode-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![MoviePy](https://img.shields.io/badge/MoviePy-v1%20%26%20v2-FF6F00?style=for-the-badge)](https://zulko.github.io/moviepy/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<p align="center">
  <a href="#-about-the-project">About</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-key-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-documentation">API Docs</a> •
  <a href="#-configuration">Configuration</a>
</p>

---

</div>

## 📖 About the Project

Creating educational explainer videos manually is a time-consuming process that requires scriptwriting, voice recording, slide design, stock asset sourcing, and video editing. Existing automated tools often rely on heavyweight rendering dependencies like LaTeX, Manim, or Blender, which take minutes per frame and require complex system-level software.

**Explain IQ** solves this with a lightweight, asynchronous Python microservice that produces complete **1080p educational videos** from just a concept title (e.g., *"Newton's Laws of Motion"* or *"Photosynthesis"*).

By combining **Google Gemini** for pedagogical scripting, **Microsoft Edge Neural Speech** for narration, **real Wikimedia Commons & Pexels photography**, and a **custom Pillow slide engine**, Explain IQ generates production-quality videos in seconds—completely dependency-free from external video renderers.

---

## 🛠️ How It Works: The 5-Stage Pipeline

```
  User Request (Concept + Audience + Depth)
                     │
                     ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Stage 1: Pedagogical Storyboarding                         │
  │  • Gemini Flash-Lite designs a structured 4-8 scene script  │
  │  • Generates narration, slide layouts, and image keywords   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Stage 2: Neural Speech & Subtitle Synthesis                │
  │  • Edge-TTS synthesizes scene voiceovers with neural audio  │
  │  • WordBoundary events capture word-level timestamps (.srt) │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Stage 3: Visual Card & Stock Photography Engine            │
  │  • Native Pillow engine renders 1080p cards & pill lists    │
  │  • Queries Wikimedia Commons & Pexels for authentic photos  │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Stage 4: Cinematic Video Assembly                          │
  │  • Ken Burns zero-copy camera drift (zoom/pan) over frames  │
  │  • Narration synchronized with 1080p visuals & crossfades   │
  │  • Ambient background audio ducked at -22 dB under voice    │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Stage 5: Delivery, Persistence & Auto-Cleanup              │
  │  • State recorded in SQLite (survives restarts)             │
  │  • Video (.mp4) and subtitles (.srt) ready for download     │
  │  • Optional Webhook callback notification dispatched        │
  └─────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features & Architecture

### 1. 🧠 Intelligent Storyboarding (Google Gemini)
* Utilizes **Gemini Flash-Lite** with native Pydantic schema enforcement (`response_schema=Storyboard`).
* Adapts video depth dynamically based on `duration_mode`:
  * **Quick (~45s)**: 3 to 4 concise overview scenes.
  * **Standard (~90s)**: 4 to 6 detailed pedagogical scenes.
  * **Deep Dive (~3–4m)**: 6 to 8 comprehensive concept scenes.

### 2. 🎙️ Natural Voiceover & Word-Level Subtitles
* Synthesizes studio-grade voiceovers using Microsoft Edge Neural TTS (`en-US-AriaNeural`).
* Captures word-level timestamp boundaries directly from the audio stream.
* Automatically merges scene timestamps into a single, synchronized **`.srt` subtitle file**.

### 3. 🖼️ Real Stock Photography (No AI Hallucinations)
* Searches **Wikimedia Commons** (zero API key required) using targeted File namespace queries.
* Downloads high-resolution 1080p educational and historical photography.
* Supports **Pexels API** as an optional primary photo source.
* Formats photos with centered 1080p crop and a sleek glassmorphic caption pill.

### 4. 🎨 Mathematical 1080p Slide Engine
* Built directly on Pillow with **zero external rendering dependencies**.
* Uses mathematical centering (`anchor="ma"`, `anchor="mm"`) anchored to screen midpoint ($x = 960$).
* **Slide Templates**:
  * **Title Card**: Bold 56px title with glowing accent stripe and category badge.
  * **Bullet Slide**: Structured individual pill cards with aligned numbered badges (`01`, `02`, `03`).
  * **Concept Card**: High-contrast callout container highlighting equations, formulas, and laws.

### 5. 🎥 Cinematic Ken Burns Motion & Audio Ducking
* Zero-copy NumPy frame slicing applies continuous, smooth camera pan and zoom drift across slides.
* Mixes ambient background music layered softly under voiceover (-22 dB ducking).
* Isolates temporary files inside `tmp/` to prevent root directory pollution.

### 6. ⚡ Production-Ready Microservice
* **Concurrency Controller**: Bounded worker semaphore (`asyncio.Semaphore(2)`) protects CPU/RAM.
* **Persistent SQLite (`jobs.db`)**: Tracks all jobs with WAL mode, surviving crashes and reboots.
* **Queue Position Tracking**: Callers receive real-time queue position while waiting.
* **Webhook Callbacks**: Dispatches HTTP POST notifications upon completion.

---

## 🚀 Quick Start

### Prerequisites
* **Python 3.10 to 3.12**
* **Google Gemini API Key** (Free tier available at [Google AI Studio](https://aistudio.google.com/app/apikey))

### 1. Clone & Install
```bash
git clone https://github.com/asjadpathan/explain_iq.git
cd explain_iq
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Create a `.env` file in the project root:
```ini
# Required: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-lite-latest

# Edge TTS voice
TTS_VOICE=en-US-AriaNeural

# Optional: Pexels API key (auto-falls back to Wikimedia Commons)
PEXELS_API_KEY=

# Worker concurrency limit
MAX_CONCURRENT_JOBS=2
```

### 3. Start the Microservice
```bash
python main.py
```
> The API will be live at **http://localhost:8000** with interactive Swagger documentation at **http://localhost:8000/docs**.

---

## 📡 API Documentation

### `POST /generate` — Create Video Job
Submits a concept for video generation. Returns `HTTP 202 Accepted` immediately with a `job_id` and queue position.

**Request Body:**
```json
{
  "concept": "Newton's Laws of Motion",
  "target_audience": "high school students",
  "duration_mode": "standard",
  "voice": "en-US-AriaNeural",
  "include_music": false,
  "webhook_url": "https://example.com/api/webhook"
}
```

**Response (`202 Accepted`):**
```json
{
  "job_id": "0ff1a676-cfd4-480d-8660-cd49a3cbe34e",
  "status": "queued",
  "queue_position": 1,
  "message": "Job queued at position 1. Poll /status/0ff1a676-cfd4-480d-8660-cd49a3cbe34e for updates."
}
```

---

### `GET /status/{job_id}` — Poll Job Progress
Track generation stages and completion status.

**Response (Completed):**
```json
{
  "job_id": "0ff1a676-cfd4-480d-8660-cd49a3cbe34e",
  "concept": "Newton's Laws of Motion",
  "target_audience": "high school students",
  "status": "completed",
  "progress_pct": 100,
  "current_stage": "Video generation complete!",
  "video_url": "/download/0ff1a676-cfd4-480d-8660-cd49a3cbe34e",
  "subtitles_url": "/subtitles/0ff1a676-cfd4-480d-8660-cd49a3cbe34e",
  "duration_seconds": 92.4,
  "created_at": "2026-10-06T16:00:52Z",
  "updated_at": "2026-10-06T16:02:18Z"
}
```

**Job Lifecycle:**
`queued` ➔ `storyboarding` ➔ `generating_audio` ➔ `generating_visuals` ➔ `assembling` ➔ `completed` *(or `failed`)*

---

### Additional Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/download/{job_id}` | Streams the completed 1080p MP4 video file. |
| `GET` | `/subtitles/{job_id}` | Downloads the synchronized `.srt` subtitle file. |
| `GET` | `/health` | Reports service health, queue depth, and stored video count. |
| `GET` | `/jobs?limit=20` | Returns recent jobs from the SQLite database with pagination. |

---

## 💻 Client Integration

```javascript
// Example: Node.js / Browser Fetch
const res = await fetch("http://localhost:8000/generate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ concept: "Photosynthesis", duration_mode: "standard" }),
});
const { job_id } = await res.json();

const timer = setInterval(async () => {
  const status = await (await fetch(`http://localhost:8000/status/${job_id}`)).json();
  console.log(`[${status.progress_pct}%] ${status.current_stage}`);

  if (status.status === "completed") {
    clearInterval(timer);
    console.log("Video URL:", `http://localhost:8000${status.video_url}`);
    console.log("Subtitles URL:", `http://localhost:8000${status.subtitles_url}`);
  }
}, 3000);
```

---

## 📁 Project Structure

```
explain_iq/
├── main.py            # FastAPI router, worker runner & life-cycle management
├── llm_service.py     # Gemini storyboarding with adaptive duration presets
├── slide_service.py   # Pillow 1080p slide card engine with mathematical centering
├── media_service.py   # Edge-TTS voiceover, SRT timestamps & stock photo fetcher
├── assembler.py       # MoviePy assembly: Ken Burns motion, ducking & temp isolation
├── database.py        # Embedded SQLite persistence layer (jobs.db)
├── config.py          # Centralized configuration & path initializations
├── requirements.txt   # Python dependencies
├── output/            # Generated .mp4 and .srt artifacts (git ignored)
├── tmp/               # Scratch directories for scene rendering (auto-cleaned)
└── jobs.db            # Embedded SQLite job store (git ignored)
```

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | *(Required)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | Model used for storyboard generation |
| `TTS_VOICE` | `en-US-AriaNeural` | Microsoft Edge neural voice |
| `PEXELS_API_KEY` | *(Optional)* | Pexels key (auto-falls back to Wikimedia Commons) |
| `MAX_CONCURRENT_JOBS`| `2` | Max parallel video rendering workers |
| `VIDEO_WIDTH` / `HEIGHT`| `1920` / `1080` | Video output resolution in pixels |
| `VIDEO_FPS` | `24` | Video frame rate |

---

## 📄 License

This project is open-source and available under the **MIT License**.
