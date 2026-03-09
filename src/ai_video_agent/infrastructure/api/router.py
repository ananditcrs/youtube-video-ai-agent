"""
API Router — FastAPI REST endpoints for the video generation pipeline.

Endpoints:
    POST /generate        — Start a new video generation pipeline (async)
    GET  /status/{job_id} — Check job status
    GET  /jobs            — List all jobs
    GET  /health          — Health check
    GET  /download/{job_id} — Download the generated video
    POST /webhook/generate — Webhook-friendly endpoint for n8n/Make/Zapier
"""

from __future__ import annotations

import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from ai_video_agent.domain.models import JobStatus, GenerateRequest, JobInfo

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Video Agent API",
    description="Topic/Script → Voiceover → Images → Video → YouTube — via REST API",
    version="2.0.0",
)


# ── In-memory job store ───────────────────────────────────────────────────────
# For production, swap this with Redis or a database.

_jobs: dict[str, JobInfo] = {}


# ── Pipeline runner ───────────────────────────────────────────────────────────

def _run_pipeline_sync(job_id: str, request: GenerateRequest) -> None:
    """Execute the video pipeline synchronously (runs in a background thread)."""
    from ai_video_agent.application.pipeline_service import run_pipeline

    job = _jobs[job_id]
    job.status = JobStatus.RUNNING

    # Prepare script file if script text was provided directly
    tmp_dir = None
    script_file = None
    if request.script:
        tmp_dir = Path(tempfile.mkdtemp(prefix="ai_video_"))
        script_file = tmp_dir / "script.txt"
        script_file.write_text(request.script, encoding="utf-8")

    try:
        result = run_pipeline(
            script_path=script_file,
            topic=request.topic,
            title=request.title,
            description=request.description,
            tags=request.tags,
            skip_images=request.skip_images,
            skip_upload=request.skip_upload,
            privacy=request.privacy,
            script_style=request.script_style,
            script_minutes=request.script_minutes,
        )
        job.status = JobStatus.COMPLETED
        job.result = result
        job.completed_at = datetime.now().isoformat()

    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.completed_at = datetime.now().isoformat()

    finally:
        if script_file:
            script_file.unlink(missing_ok=True)
        if tmp_dir:
            tmp_dir.rmdir()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-video-agent", "timestamp": datetime.now().isoformat()}


@app.post("/generate", response_model=JobInfo, status_code=202)
async def generate_video(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Start a new video generation pipeline.

    Provide either:
    - `script`: Full voiceover script text, OR
    - `topic`: A topic/description and GPT-4o will generate the script (Step 1)

    The pipeline runs asynchronously in the background. Use the returned
    job_id to poll /status/{job_id} for progress.
    """
    if not request.script and not request.topic:
        raise HTTPException(
            status_code=422,
            detail="Provide either 'script' (full text) or 'topic' (AI generates the script)",
        )
    job_id = str(uuid.uuid4())[:8]
    job = JobInfo(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=datetime.now().isoformat(),
        request=request.model_dump(),
    )
    _jobs[job_id] = job

    background_tasks.add_task(_run_pipeline_sync, job_id, request)

    return job


@app.get("/status/{job_id}", response_model=JobInfo)
async def get_status(job_id: str):
    """Check the status of a video generation job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return _jobs[job_id]


@app.get("/jobs")
async def list_jobs():
    """List all jobs (most recent first)."""
    sorted_jobs = sorted(_jobs.values(), key=lambda j: j.created_at, reverse=True)
    return {"jobs": sorted_jobs, "total": len(sorted_jobs)}


@app.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download the generated video file for a completed job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = _jobs[job_id]
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Job {job_id} is {job.status.value}, not completed")

    video_path = job.result.get("steps", {}).get("video", {}).get("path")
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=Path(video_path).name,
    )


@app.post("/webhook/generate")
async def webhook_generate(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Webhook-friendly endpoint for external orchestrators (n8n, Make, Zapier).
    Same as /generate but returns a simpler response.
    """
    if not request.script and not request.topic:
        raise HTTPException(
            status_code=422,
            detail="Provide either 'script' (full text) or 'topic' (AI generates the script)",
        )
    job_id = str(uuid.uuid4())[:8]
    job = JobInfo(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=datetime.now().isoformat(),
        request=request.model_dump(),
    )
    _jobs[job_id] = job
    background_tasks.add_task(_run_pipeline_sync, job_id, request)

    return {
        "job_id": job_id,
        "status": "queued",
        "poll_url": f"/status/{job_id}",
        "download_url": f"/download/{job_id}",
    }
