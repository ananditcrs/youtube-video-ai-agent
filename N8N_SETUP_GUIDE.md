# n8n Workflow — AI Video Agent Setup Guide

## Workflow Overview

```
┌──────────────┐    ┌─────────────┐    ┌───────────────────┐    ┌──────────────┐
│   Webhook    │───▶│  Prepare    │───▶│  Start Pipeline   │───▶│  Respond to  │
│   Trigger    │    │  Request    │    │  POST /generate   │    │  Webhook     │
└──────────────┘    └─────────────┘    └────────┬──────────┘    └──────────────┘
                                                │
                                     ┌──────────▼──────────┐
                              ┌─────▶│  Poll Job Status    │◀────────┐
                              │      │  GET /status/{id}   │         │
                              │      └──────────┬──────────┘         │
                              │                 │                    │
                              │      ┌──────────▼──────────┐  ┌─────┴──────┐
                              │      │   Is Completed?     │  │  Wait 30s  │
                              │      └──┬──────────────┬───┘  └────────────┘
                              │    YES  │              │  NO         ▲
                              │         ▼              └─────────────┘
                              │  ┌──────────────┐
                              │  │  Is Failed?  │
                              │  └──┬────────┬──┘
                              │ YES │        │ NO
                              │     ▼        ▼
                              │  ┌──────┐ ┌──────────────┐
                              │  │Slack │ │Download Video│
                              │  │Alert │ └──────┬───────┘
                              │  └──────┘        │
                              │           ┌──────▼───────┐
                              │           │  Notify      │
                              │           │  (Telegram/  │
                              │           │   Email)     │
                              │           └──────────────┘
```

## Quick Start

### 1. Install n8n (free, self-hosted)

```bash
# Option A: npm (simplest)
npm install -g n8n
n8n start

# Option B: Docker
docker run -it --rm -p 5678:5678 n8nio/n8n

# Option C: Docker Compose (persistent)
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
```

n8n UI opens at **http://localhost:5678**

### 2. Import the Workflow

1. Open n8n → **Workflows** → **Add workflow** → **Import from File**
2. Select `n8n-workflow-template.json` from this project
3. The workflow appears with all nodes pre-configured

### 3. Set Environment Variable

In n8n, go to **Settings** → **Variables** and add:

| Variable | Value | Example |
|----------|-------|---------|
| `AI_VIDEO_AGENT_URL` | Your API base URL | `http://localhost:8000` or `https://your-app.railway.app` |

### 4. Start Your API

Make sure the AI Video Agent API is running:

```bash
# Local
cd d:\workspace\ai-video-agent
uvicorn api:app --host 0.0.0.0 --port 8000

# Or Docker
docker compose up --build
```

### 5. Test It

```bash
# Trigger the webhook
curl -X POST http://localhost:5678/webhook/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Welcome to the future of AI. Today we explore the top 10 trends...",
    "title": "AI Trends 2026",
    "skip_upload": true
  }'
```

---

## Node Reference

| Node | Purpose | Config Needed |
|------|---------|---------------|
| **Webhook Trigger** | Receives POST requests to start a video | None (auto-generates URL) |
| **Schedule Trigger** | Auto-runs weekly (disabled by default) | Enable + set cron |
| **Prepare Request** | Normalizes input parameters | None |
| **Start Video Pipeline** | Calls `POST /generate` on your API | Set `AI_VIDEO_AGENT_URL` |
| **Poll Job Status** | Calls `GET /status/{job_id}` in a loop | None |
| **Is Completed?** | Routes based on job status | None |
| **Wait 30 Seconds** | Pauses between polls | Adjust if needed |
| **Is Failed?** | Catches failures | None |
| **Download Video** | Gets the MP4 from `/download/{job_id}` | None |
| **Notify (Telegram)** | Sends success message | Enable + add bot token |
| **Notify (Email)** | Sends email on completion | Enable + SMTP config |
| **Notify (Slack)** | Sends failure alert | Enable + Slack OAuth |

---

## Optional: Enable Notifications

### Telegram
1. Create a bot via [@BotFather](https://t.me/botfather)
2. In n8n: **Credentials** → **Telegram API** → add bot token
3. Set `TELEGRAM_CHAT_ID` in n8n variables
4. Enable the "Notify Success (Telegram)" node

### Slack
1. Create a [Slack App](https://api.slack.com/apps) with `chat:write` scope
2. In n8n: **Credentials** → **Slack OAuth2** → add token
3. Set `SLACK_CHANNEL` in n8n variables (default: `#video-alerts`)
4. Enable the "Notify Failure (Slack)" node

### Email
1. In n8n: **Credentials** → **SMTP** → add your mail server details
2. Set `NOTIFICATION_EMAIL` in n8n variables
3. Enable the "Notify Success (Email)" node

---

## Extending the Workflow

### Add Google Drive Upload
Insert a **Google Drive** node after "Download Video" to auto-save videos.

### Add Human Approval
Insert a **Wait for Approval** node before "Start Video Pipeline" to review scripts before generating.

### Add Script from Google Sheets
Replace the webhook trigger with a **Google Sheets Trigger** that watches for new rows, pulling scripts automatically.

### Add Thumbnail Generation
Add a parallel branch after "Start Video Pipeline" that calls a DALL-E/Midjourney API for custom thumbnails.
