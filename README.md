# 🎬 Explain IQ — AI Educational Video Generation Microservice

Explain IQ is an automated video generation engine that transforms educational topics into 1080p explainer videos complete with structured storyboards, AI voiceover, educational graphic slides, and synchronized video assembly.

---

## 🚀 Key Features

- **Gemini Storyboarding**: Generates structured, pedagogical scene-by-scene scripts tailored to target audiences.
- **Natural Neural TTS**: Uses Microsoft Edge Neural TTS (`edge-tts`) for clear, human-like voiceovers.
- **Native Slide & Visual Engine**: Renders crisp 1920×1080 title cards, bullet lists, concept/equation callouts, and illustrative scenes using Pillow (no heavy external dependencies like LaTeX or Manim required).
- **Automated Video Assembly**: MoviePy pipeline with audio-visual synchronization, transitions, and H.264/AAC MP4 output.
- **Asynchronous Job Pipeline**: FastAPI microservice with instant job queuing, status tracking, and CORS support for frontend integration.

---

## 🛠️ Architecture & Pipeline

```
  User Concept Request
         │
         ▼
[1. Storyboard Generation]  ──► Google Gemini API (gemini-flash-lite-latest)
         │
         ▼
[2. Voiceover Synthesis]   ──► Edge-TTS (en-US-AriaNeural) → Scene MP3s
         │
         ▼
[3. Visual Slide Rendering] ──► Pillow Slide Engine → 1080p Graphic PNGs
         │
         ▼
[4. Final MP4 Assembly]    ──► MoviePy / FFmpeg → output/{job_id}.mp4
```

---

## 📋 Prerequisites

- **Python 3.10 to 3.12**
- **Google Gemini API Key** (Free at [Google AI Studio](https://aistudio.google.com/app/apikey))
- **Internet access** (for Gemini API and Edge-TTS voiceover synthesis)

---

## ⚡ Quick Start

### 1. Clone & Navigate to Directory
```bash
git clone https://github.com/asjadpathan/explain_iq.git
cd explain_iq
```

### 2. (Optional) Create and Activate Virtual Environment
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create or verify your `.env` file in the project root:

```ini
# Google AI Studio API Key (Get from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Recommended model with generous free quotas
GEMINI_MODEL=gemini-flash-lite-latest

# Voiceover voice (e.g. en-US-AriaNeural, en-US-GuyNeural, en-GB-SoniaNeural)
TTS_VOICE=en-US-AriaNeural

# Video output settings
VIDEO_WIDTH=1920
VIDEO_HEIGHT=1080
VIDEO_FPS=24

# Output and temp directories
OUTPUT_DIR=./output
TEMP_DIR=./tmp
```

---

## ▶️ Running the Microservice

### Method 1: Direct Python Execution
```powershell
python main.py
```

### Method 2: Uvicorn Server Command
```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Once started, the API is available at:
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 📡 API Reference & Usage

### 1. Health Check
Checks if the service is running and reports active jobs.

- **URL**: `GET /health`
- **Response**:
```json
{
  "status": "healthy",
  "service": "explain_iq",
  "active_jobs": 0,
  "total_jobs": 2
}
```

---

### 2. Start Video Generation
Dispatches a video generation job to the background queue.

- **URL**: `POST /generate`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "concept": "Newton's Laws of Motion",
  "target_audience": "high school students"
}
```

- **PowerShell Example**:
```powershell
$body = @{
    concept = "Newton's Laws of Motion"
    target_audience = "high school students"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/generate" -Method Post -ContentType "application/json" -Body $body
```

- **cURL Example**:
```bash
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{"concept": "Photosynthesis", "target_audience": "middle school"}'
```

- **Response (HTTP 202 Accepted)**:
```json
{
  "job_id": "0ff1a676-cfd4-480d-8660-cd49a3cbe34e",
  "status": "queued",
  "message": "Video generation started. Poll /status/0ff1a676-cfd4-480d-8660-cd49a3cbe34e for progress."
}
```

---

### 3. Poll Job Progress
Track generation stages and completion status.

- **URL**: `GET /status/{job_id}`
- **PowerShell Example**:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/status/<job_id>"
```

- **Response (In Progress)**:
```json
{
  "job_id": "0ff1a676-cfd4-480d-8660-cd49a3cbe34e",
  "status": "generating_visuals",
  "progress_pct": 55,
  "current_stage": "Visuals: scene 2/5 (slide)",
  "error": null,
  "video_url": null,
  "created_at": "2026-09-22T06:00:52Z",
  "updated_at": "2026-09-22T06:01:20Z"
}
```

- **Response (Completed)**:
```json
{
  "job_id": "0ff1a676-cfd4-480d-8660-cd49a3cbe34e",
  "status": "completed",
  "progress_pct": 100,
  "current_stage": "Video generation complete!",
  "error": null,
  "video_url": "/download/0ff1a676-cfd4-480d-8660-cd49a3cbe34e"
}
```

**Job Status Lifecycle:**
`queued` ➔ `storyboarding` ➔ `generating_audio` ➔ `generating_visuals` ➔ `assembling` ➔ `completed` (or `failed`)

---

### 4. Download Completed Video
Streams the generated 1080p MP4 file.

- **URL**: `GET /download/{job_id}`
- **Browser/VLC**: Open `http://localhost:8000/download/{job_id}` directly in your browser or video player.
- **PowerShell Download**:
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/download/<job_id>" -OutFile "output_video.mp4"
```

---

## 💻 Frontend Integration (React / Next.js / Vite)

CORS is enabled by default (`allow_origins=["*"]`). You can call the API directly from JavaScript:

```javascript
// 1. Trigger video creation
const startRes = await fetch("http://localhost:8000/generate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ concept: "The Water Cycle", target_audience: "elementary" })
});
const { job_id } = await startRes.json();

// 2. Poll progress until completed
const timer = setInterval(async () => {
  const statusRes = await fetch(`http://localhost:8000/status/${job_id}`);
  const data = await statusRes.json();
  
  console.log(`Progress: ${data.progress_pct}% — ${data.current_stage}`);
  
  if (data.status === "completed") {
    clearInterval(timer);
    // 3. Display or download video
    const videoUrl = `http://localhost:8000${data.video_url}`;
    document.getElementById("videoPlayer").src = videoUrl;
  } else if (data.status === "failed") {
    clearInterval(timer);
    console.error("Pipeline failed:", data.error);
  }
}, 3000);
```

---

## 📁 Project Directory Structure

```
explain_iq/
├── .env                  # API keys and environment configuration (ignored by git)
├── .env.example          # Environment template with placeholder values
├── .gitignore            # Git ignore rules for virtual environments, outputs & secrets
├── config.py             # Centralized settings loader
├── main.py               # FastAPI application & pipeline orchestration
├── llm_service.py        # Gemini storyboarding service
├── slide_service.py      # 1080p educational slide graphics generator
├── media_service.py      # Edge-TTS voiceover & illustrative image generation
├── assembler.py          # Video/audio synchronizer & MP4 compiler
├── manim_templates.py    # Compatibility shim delegating to slide_service
├── requirements.txt      # Python dependencies
├── output/               # Rendered final .mp4 videos (git ignored)
└── tmp/                  # Temporary scene assets (cleaned up automatically, git ignored)
```

---

## ⚙️ Configuration Options

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | *(Required)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | Model used for storyboarding |
| `TTS_VOICE` | `en-US-AriaNeural` | Microsoft Edge neural voice |
| `VIDEO_WIDTH` | `1920` | Output video width in pixels |
| `VIDEO_HEIGHT` | `1080` | Output video height in pixels |
| `VIDEO_FPS` | `24` | Video frame rate |
| `OUTPUT_DIR` | `./output` | Destination for generated videos |
| `TEMP_DIR` | `./tmp` | Working directory for scene assets |

To see all available voices for `TTS_VOICE`:
```bash
python -m edge_tts --list-voices
```

---

## 🔧 Troubleshooting

- **No visuals in output video?**
  Ensure the latest `assembler.py` and `slide_service.py` are loaded. The video generation now produces full 1080p visual streams with both graphic slides and illustrative scenes.
- **Error: 429 Quota Exceeded from Gemini?**
  Ensure `GEMINI_MODEL=gemini-flash-lite-latest` in `.env`. This model provides the highest free-tier rate limits and availability.
- **Port 8000 already in use?**
  Run `python -m uvicorn main:app --port 8001` or free the port on Windows using:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 | Stop-Process -Id { $_.OwningProcess } -Force
  ```


---

## 💡 Automated PowerShell Workflow Example

```powershell
# 1. Dispatch generation job
$body = @{
    concept = "Machine Learning"
    target_audience = "high school students"
} | ConvertTo-Json

$job = Invoke-RestMethod -Uri "http://127.0.0.1:8000/generate" -Method Post -ContentType "application/json" -Body $body
Write-Host "Dispatched Job ID: $($job.job_id)" -ForegroundColor Green

# 2. Poll until completion
do {
    $status = Invoke-RestMethod -Uri "http://127.0.0.1:8000/status/$($job.job_id)"
    Write-Host "$($status.progress_pct)% — $($status.current_stage)" -ForegroundColor Cyan
    Start-Sleep -Seconds 3
} while ($status.status -ne "completed" -and $status.status -ne "failed")

# 3. Download final video
if ($status.status -ne "failed") {
    $downloadUrl = "http://127.0.0.1:8000$($status.video_url)"
    Invoke-WebRequest -Uri $downloadUrl -OutFile "explain_iq_$($job.job_id).mp4"
    Write-Host "Downloaded to explain_iq_$($job.job_id).mp4" -ForegroundColor Green
}
```

