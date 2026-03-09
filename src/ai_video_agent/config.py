"""
AI Video Agent — Configuration
Loads settings from .env and provides typed config objects.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env from project root ──────────────────────────────────────────────
# config.py lives at src/ai_video_agent/config.py → project root is 3 levels up
_PKG_DIR = Path(__file__).resolve().parent
_ROOT = _PKG_DIR.parent.parent
load_dotenv(_ROOT / ".env")


def _env(key: str, default: str | None = None) -> str:
    val = os.getenv(key, default)
    if val is None:
        raise EnvironmentError(f"Missing required env var: {key}  (set it in .env)")
    return val


def _env_float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


def _env_int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class ElevenLabsConfig:
    api_key: str = field(default_factory=lambda: _env("ELEVENLABS_API_KEY"))
    voice_id: str = field(default_factory=lambda: _env("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"))
    model: str = field(default_factory=lambda: _env("ELEVENLABS_MODEL", "eleven_multilingual_v2"))
    stability: float = field(default_factory=lambda: _env_float("ELEVENLABS_STABILITY", 0.50))
    similarity: float = field(default_factory=lambda: _env_float("ELEVENLABS_SIMILARITY", 0.80))
    style: float = field(default_factory=lambda: _env_float("ELEVENLABS_STYLE", 0.25))


@dataclass
class OpenAIConfig:
    api_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY"))
    image_model: str = field(default_factory=lambda: _env("OPENAI_IMAGE_MODEL", "dall-e-3"))
    image_size: str = field(default_factory=lambda: _env("OPENAI_IMAGE_SIZE", "1792x1024"))
    image_quality: str = field(default_factory=lambda: _env("OPENAI_IMAGE_QUALITY", "hd"))


@dataclass
class VideoConfig:
    width: int = field(default_factory=lambda: _env_int("VIDEO_WIDTH", 1920))
    height: int = field(default_factory=lambda: _env_int("VIDEO_HEIGHT", 1080))
    fps: int = field(default_factory=lambda: _env_int("VIDEO_FPS", 30))
    image_duration: int = field(default_factory=lambda: _env_int("IMAGE_DISPLAY_DURATION", 5))
    fade_duration: float = field(default_factory=lambda: _env_float("FADE_DURATION", 0.5))
    bg_music_volume: float = field(default_factory=lambda: _env_float("BACKGROUND_MUSIC_VOLUME", 0.12))


@dataclass
class YouTubeConfig:
    client_secret_file: str = field(
        default_factory=lambda: _env("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")
    )
    category_id: str = field(default_factory=lambda: _env("YOUTUBE_CATEGORY_ID", "28"))
    privacy: str = field(default_factory=lambda: _env("YOUTUBE_PRIVACY", "private"))
    token_file: str = "youtube_token.json"


@dataclass
class Paths:
    root: Path = _ROOT
    output: Path = _ROOT / "output"
    audio: Path = _ROOT / "output" / "audio"
    images: Path = _ROOT / "output" / "images"
    footage: Path = _ROOT / "output" / "footage"
    video: Path = _ROOT / "output" / "video"
    thumbnails: Path = _ROOT / "output" / "thumbnails"

    def ensure_dirs(self) -> None:
        """Create all output directories if they don't exist."""
        for p in [self.output, self.audio, self.images, self.footage, self.video, self.thumbnails]:
            p.mkdir(parents=True, exist_ok=True)


# ── Singletons ───────────────────────────────────────────────────────────────

elevenlabs_cfg = ElevenLabsConfig()
openai_cfg = OpenAIConfig()
video_cfg = VideoConfig()
youtube_cfg = YouTubeConfig()
paths = Paths()
