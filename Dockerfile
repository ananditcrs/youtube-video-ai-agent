# ── AI Video Agent — Production Dockerfile ────────────────────────────────────
# Multi-stage build: slim Python base + FFmpeg for MoviePy video assembly.
#
# Build:  docker build -t ai-video-agent .
# Run:    docker run --env-file .env -p 8000:8000 ai-video-agent
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS base

# Install FFmpeg (required by MoviePy) and clean up apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project manifest and install dependencies
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

# Create output directories
RUN mkdir -p output/audio output/images output/footage output/video output/thumbnails output/scripts

# Copy supplementary files (n8n workflows, docs, etc.)
COPY .env.example .
COPY *.json .
COPY *.md .

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the API server
CMD ["uvicorn", "ai_video_agent.infrastructure.api.router:app", "--host", "0.0.0.0", "--port", "8000"]
