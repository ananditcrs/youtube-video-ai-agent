# AI Video Agent

**Topic → Script → Voiceover → Images → Video → YouTube — fully automated.**

An end-to-end AI video production pipeline built with clean architecture:

1. **Generates a script** from a topic using **GPT-4o**
2. **Generates AI voiceover** using **ElevenLabs**
3. **Generates AI visuals** using **OpenAI DALL-E 3**
4. **Assembles a polished video** with **MoviePy** (Ken Burns effect, transitions, text overlays)
5. **Uploads the final video** to **YouTube** via the Data API v3

One command. Zero camera. Zero editing.

---

## Project Structure

```
ai-video-agent/
├── pyproject.toml                          # Project manifest & dependencies
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── src/
│   └── ai_video_agent/
│       ├── __init__.py                     # Package (version info)
│       ├── __main__.py                     # python -m ai_video_agent
│       ├── config.py                       # Configuration loader (.env)
│       ├── main.py                         # CLI entry point (argparse)
│       │
│       ├── domain/                         # Pure data — no external deps
│       │   ├── models.py                   # Pydantic models (JobStatus, GenerateRequest, JobInfo)
│       │   ├── prompts.py                  # System prompts & default image prompts
│       │   └── defaults.py                 # Default title, description, tags
│       │
│       ├── application/                    # Business logic & orchestration
│       │   ├── pipeline_service.py         # run_pipeline() — 5-step orchestrator
│       │   ├── script_service.py           # GPT-4o script generation
│       │   ├── voiceover_service.py        # ElevenLabs text-to-speech
│       │   ├── image_service.py            # DALL-E 3 image generation
│       │   ├── video_service.py            # MoviePy video assembly
│       │   └── youtube_service.py          # YouTube Data API upload
│       │
│       └── infrastructure/                 # External interfaces
│           ├── api/
│           │   └── router.py               # FastAPI REST endpoints
│           └── monitoring/
│               └── logger.py               # Structured logging
│
├── tests/
│   └── test_pipeline_service.py            # Unit tests
│
└── output/                                 # Generated assets (auto-created)
    ├── audio/
    ├── images/
    ├── video/
    └── thumbnails/
```

---

## Quick Start

### 1. Prerequisites

- **Python 3.10+**
- **FFmpeg** — required by MoviePy for video encoding
  ```bash
  # Windows (via winget)
  winget install FFmpeg

  # macOS
  brew install ffmpeg

  # Verify
  ffmpeg -version
  ```

### 2. Install

```bash
cd ai-video-agent
pip install -e .
```

### 3. Configure API Keys

```bash
cp .env.example .env   # or: copy .env.example .env  (Windows)
```

Edit `.env` and add your API keys:

| Key | Where to Get It |
|-----|-----------------|
| `ELEVENLABS_API_KEY` | [elevenlabs.io/settings/api-keys](https://elevenlabs.io/settings/api-keys) |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| YouTube OAuth | See "YouTube Setup" section below |

### 4. Run the Agent

```bash
# Generate from a topic (script is auto-generated via GPT-4o)
ai-video-agent --topic "10 AI Trends for 2026"

# Or use python -m
python -m ai_video_agent --topic "10 AI Trends for 2026"

# From an existing script file
ai-video-agent path/to/your-script.txt

# Skip YouTube upload
ai-video-agent --topic "AI Tools" --skip-upload

# Skip image generation (reuse existing images)
ai-video-agent script.txt --skip-images

# Upload as public with custom title
ai-video-agent script.txt --title "My Video Title" --privacy public

# Add background music and thumbnail
ai-video-agent script.txt --music bg_track.mp3 --thumbnail thumb.png
```

---

## Detailed Setup

### ElevenLabs Setup

1. Create account at [elevenlabs.io](https://elevenlabs.io)
2. Go to **Settings** → **API Keys** → Copy your key
3. Choose a voice:
   - Go to **Voices** → click a voice → copy the **Voice ID** from the URL
   - Default: `pNInz6obpgDQGcFmaJgB` (Adam — deep authoritative male)
   - Alternatives: Rachel (female), Josh (younger male)
4. Add to `.env`:
   ```env
   ELEVENLABS_API_KEY=your_key_here
   ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB
   ```

**Pricing**: Free = 10 min/month, Starter = $5/month (30 min)

### OpenAI Setup

1. Create account at [platform.openai.com](https://platform.openai.com)
2. Go to **API Keys** → Create new key → Copy
3. Add billing (DALL-E 3 costs ~$0.04–$0.08 per image)
4. Add to `.env`:
   ```env
   OPENAI_API_KEY=sk-your_key_here
   ```

**Cost estimate**: 25 images × $0.08 = ~$2.00 per video

### YouTube Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select existing)
3. Enable the **YouTube Data API v3**:
   - APIs & Services → Library → Search "YouTube Data API v3" → Enable
4. Create OAuth 2.0 credentials:
   - APIs & Services → Credentials → Create Credentials → OAuth Client ID
   - Application type: **Desktop App**
   - Download the JSON file
5. Save as `client_secret.json` in the project root:
   ```
   ai-video-agent/
   └── client_secret.json   ← here
   ```
6. **First run**: A browser window will open asking you to sign in and grant YouTube upload permission
7. After first auth, a `youtube_token.json` is saved — subsequent runs authenticate automatically

---

## Usage Examples

### Generate from a Topic (Fully Automated)

```bash
# GPT-4o generates the script, then the full pipeline runs
ai-video-agent --topic "10 AI Trends for 2026"
```

This will:
1. Generate a YouTube script via GPT-4o
2. Generate voiceover via ElevenLabs
3. Generate 25 AI images via DALL-E 3 (takes ~5 min due to rate limits)
4. Assemble a 12–15 min video with transitions and Ken Burns effect
5. Upload to your YouTube channel as **private** (change with `--privacy public`)

### Use an Existing Script File

```bash
ai-video-agent path/to/your-script.txt
```

### Use Custom Image Prompts

Create a `my_prompts.json`:
```json
[
  {"id": "intro_01", "prompt": "A futuristic city at sunset with flying cars, 16:9, cinematic"},
  {"id": "topic_02", "prompt": "A robot teaching a classroom of students, 16:9, photorealistic"}
]
```

```bash
ai-video-agent script.txt --prompts my_prompts.json
```

---

## Configuration Reference

All settings in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ELEVENLABS_API_KEY` | *(required)* | ElevenLabs API key |
| `ELEVENLABS_VOICE_ID` | `pNInz6obpgDQGcFmaJgB` | Voice to use (Adam) |
| `ELEVENLABS_MODEL` | `eleven_multilingual_v2` | TTS model |
| `ELEVENLABS_STABILITY` | `0.50` | Voice stability (0–1) |
| `ELEVENLABS_SIMILARITY` | `0.80` | Voice similarity boost (0–1) |
| `ELEVENLABS_STYLE` | `0.25` | Style exaggeration (0–1) |
| `OPENAI_API_KEY` | *(required)* | OpenAI API key |
| `OPENAI_IMAGE_MODEL` | `dall-e-3` | Image model |
| `OPENAI_IMAGE_SIZE` | `1792x1024` | Image size |
| `OPENAI_IMAGE_QUALITY` | `hd` | Image quality |
| `VIDEO_WIDTH` | `1920` | Output video width |
| `VIDEO_HEIGHT` | `1080` | Output video height |
| `VIDEO_FPS` | `30` | Frames per second |
| `IMAGE_DISPLAY_DURATION` | `5` | Default seconds per image |
| `FADE_DURATION` | `0.5` | Cross-fade transition duration |
| `BACKGROUND_MUSIC_VOLUME` | `0.12` | Music volume (0–1) |
| `YOUTUBE_CATEGORY_ID` | `28` | Category (28 = Science & Tech) |
| `YOUTUBE_PRIVACY` | `private` | Default privacy status |

---

## Cost Per Video

| Service | Cost | Notes |
|---------|------|-------|
| ElevenLabs | $0–$5 | Free tier = 10 min, Starter = $5/mo |
| DALL-E 3 | ~$2.00 | 25 images × $0.08 |
| YouTube API | Free | YouTube Data API has generous free quota |
| MoviePy/FFmpeg | Free | Open source |
| **Total** | **~$2–$7** | Per video |

---

## Pipeline Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  💡 Topic    │───▶│  📝 Script  │───▶│  🎙️ Voice   │───▶│  🖼️ Images  │───▶│  🎬 Video   │
│  (GPT-4o)   │    │  (.txt)      │    │ (ElevenLabs) │    │  (DALL-E 3)  │    │  (MoviePy)   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                                       │
                                                                                       ▼
                                                                                ┌──────────────┐
                                                                                │  📤 YouTube  │
                                                                                │  (Data API)  │
                                                                                └──────────────┘
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `FFmpeg not found` | Install FFmpeg and ensure it's in your PATH |
| `ElevenLabs 401` | Check your API key in `.env` |
| `DALL-E rate limit` | The agent auto-waits 10s between images; reduce prompts if needed |
| `YouTube upload fails` | Ensure `client_secret.json` exists and re-authenticate |
| `MoviePy font error` | Title overlay will be skipped automatically; install fonts if needed |
| `Token expired` | Delete `youtube_token.json` and re-run for fresh auth |

---

## Online Deployment

The agent can be deployed as a REST API via Docker, or run serverlessly via GitHub Actions.

### Option 1: Docker (Railway / Render / Fly.io / any VPS)

```bash
# Build and run locally
docker compose up --build

# The API is now live at http://localhost:8000
# Interactive docs at  http://localhost:8000/docs
```

**Deploy to Railway (free $5/mo credit):**
```bash
# Install Railway CLI, then:
railway login
railway init
railway up
```

**Deploy to Render (free tier):**
1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service → connect your repo
3. Render auto-detects `Dockerfile` — set environment variables in the dashboard

**Deploy to Fly.io (3 free VMs):**
```bash
fly launch      # auto-detects Dockerfile
fly secrets set ELEVENLABS_API_KEY=xxx OPENAI_API_KEY=xxx
fly deploy
```

### Option 2: GitHub Actions (100% free)

No server needed — runs on GitHub's infrastructure.

1. **Add secrets** to your repo → Settings → Secrets → Actions:
   - `ELEVENLABS_API_KEY`
   - `OPENAI_API_KEY`
   - `YOUTUBE_TOKEN_JSON` (optional, for auto-upload)

2. **Trigger manually:** Actions tab → "Generate AI Video" → Run workflow → paste your script

3. **Download result:** The video is uploaded as a GitHub Artifact (kept for 7 days)

### API Endpoints

Once deployed, the REST API provides:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate` | Start video generation (async, returns job_id) |
| `GET` | `/status/{job_id}` | Poll job status |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/download/{job_id}` | Download completed video |
| `POST` | `/webhook/generate` | Webhook-friendly endpoint for n8n/Make/Zapier |
| `GET` | `/health` | Health check |

**Example — trigger via curl:**
```bash
# Generate from a topic
curl -X POST https://your-app.railway.app/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "5 Ways AI is Changing Healthcare",
    "title": "AI Healthcare Revolution",
    "skip_upload": true
  }'
# Returns: { "job_id": "a1b2c3d4", "status": "queued", ... }

# Or generate from a full script
curl -X POST https://your-app.railway.app/generate \
  -H "Content-Type: application/json" \
  -d '{"script": "Welcome to the future of AI..."}'

# Poll status:
curl https://your-app.railway.app/status/a1b2c3d4

# Download when complete:
curl -o video.mp4 https://your-app.railway.app/download/a1b2c3d4
```

---

## Development

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run the API server locally
uvicorn ai_video_agent.infrastructure.api.router:app --reload
```

---

## License

MIT — use freely for your content creation projects.
