<div align="center">

# 🎬 Explain IQ

**FastAPI microservice that generates 1080p educational explainer videos from a single prompt.**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini-Flash--Lite-4285F4?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## ⚡ Features

* **🧠 Gemini Storyboarding**: Structured scene-by-scene script generation.
* **🎙️ Edge Neural TTS**: Clear, human-like voiceover + synchronized `.srt` subtitles.
* **🖼️ Real Stock Photos**: Automatically fetches relevant images from Wikimedia Commons & Pexels.
* **🎨 1080p Native Slides**: High-res cards, bullet lists, and formulas rendered via Pillow.
* **🎥 Ken Burns Motion**: Smooth camera zoom and pan motion on all visual scenes.
* **💾 Persistent SQLite**: Background jobs and queue progress survive server restarts.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
git clone https://github.com/asjadpathan/explain_iq.git
cd explain_iq
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-lite-latest
TTS_VOICE=en-US-AriaNeural
MAX_CONCURRENT_JOBS=2
```

### 3. Run the Server
```bash
python main.py
```
> API available at **http://localhost:8000** (Swagger docs at `/docs`).

---

## 📡 API Usage

### Start Video Generation
```bash
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "concept": "Newton'\''s Laws of Motion",
       "target_audience": "high school students",
       "duration_mode": "standard"
     }'
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

### Check Progress & Download
```bash
# Check status
curl "http://localhost:8000/status/{job_id}"

# Download video (.mp4)
curl -O "http://localhost:8000/download/{job_id}"

# Download subtitles (.srt)
curl -O "http://localhost:8000/subtitles/{job_id}"
```

---

## ⚙️ Key Configuration Options

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | *(Required)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | Model used for storyboarding |
| `TTS_VOICE` | `en-US-AriaNeural` | Microsoft Edge neural voice |
| `PEXELS_API_KEY` | *(Optional)* | Pexels key (auto-falls back to Wikimedia Commons) |
| `MAX_CONCURRENT_JOBS`| `2` | Max parallel video rendering workers |
| `VIDEO_WIDTH` / `HEIGHT`| `1920` / `1080` | Video output resolution |

---

## 📁 Project Structure

```
explain_iq/
├── main.py            # FastAPI endpoints & queue runner
├── llm_service.py     # Gemini storyboarding
├── slide_service.py   # 1080p slide card renderer
├── media_service.py   # Edge-TTS voiceover & stock photo fetcher
├── assembler.py       # MoviePy assembly & Ken Burns motion
├── database.py        # SQLite persistent job store
├── config.py          # Environment settings
├── output/            # Generated .mp4 and .srt files
└── jobs.db            # Embedded database
```

---

## 📄 License
MIT License.
