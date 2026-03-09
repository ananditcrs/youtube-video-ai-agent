"""
Voiceover Service — Generate AI voiceover audio from scripts using ElevenLabs.
Step 2 of the pipeline.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Optional

from elevenlabs import ElevenLabs, VoiceSettings
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ai_video_agent.config import elevenlabs_cfg, paths

console = Console()

# ElevenLabs has a ~5000 character limit per request — we split longer scripts
MAX_CHARS_PER_CHUNK = 4500


def _split_script_into_chunks(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> list[str]:
    """
    Split a script into chunks at paragraph boundaries,
    keeping each chunk under max_chars.
    """
    paragraphs = re.split(r"\n\s*\n", text.strip())
    chunks: list[str] = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current_chunk and (len(current_chunk) + len(para) + 2) > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def generate_voiceover(
    script_text: str,
    output_dir: Optional[Path] = None,
    filename_prefix: str = "voiceover",
) -> list[Path]:
    """
    Generate voiceover audio from script text using ElevenLabs.

    Args:
        script_text: The full narration script (plain text).
        output_dir: Directory to save audio files. Defaults to paths.audio.
        filename_prefix: Prefix for output filenames.

    Returns:
        List of Paths to the generated MP3 files (one per chunk).
    """
    output_dir = output_dir or paths.audio
    output_dir.mkdir(parents=True, exist_ok=True)

    client = ElevenLabs(api_key=elevenlabs_cfg.api_key)

    chunks = _split_script_into_chunks(script_text)
    console.print(f"\n[bold cyan]🎙️  ElevenLabs Voiceover Generator[/]")
    console.print(f"   Script length : {len(script_text):,} characters")
    console.print(f"   Chunks        : {len(chunks)}")
    console.print(f"   Voice ID      : {elevenlabs_cfg.voice_id}")
    console.print(f"   Model         : {elevenlabs_cfg.model}\n")

    audio_files: list[Path] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for i, chunk in enumerate(chunks, 1):
            task = progress.add_task(f"Generating chunk {i}/{len(chunks)} ({len(chunk)} chars)…")

            voice_settings = VoiceSettings(
                stability=elevenlabs_cfg.stability,
                similarity_boost=elevenlabs_cfg.similarity,
                style=elevenlabs_cfg.style,
                use_speaker_boost=True,
            )

            audio_generator = client.text_to_speech.convert(
                voice_id=elevenlabs_cfg.voice_id,
                text=chunk,
                model_id=elevenlabs_cfg.model,
                voice_settings=voice_settings,
                output_format="mp3_44100_128",
            )

            # Collect bytes from the generator
            audio_bytes = b"".join(audio_generator)

            out_path = output_dir / f"{filename_prefix}_{i:02d}.mp3"
            out_path.write_bytes(audio_bytes)
            audio_files.append(out_path)

            progress.update(task, completed=True)
            console.print(f"   ✅ Saved: {out_path.name} ({len(audio_bytes):,} bytes)")

            # Small delay to respect rate limits
            if i < len(chunks):
                time.sleep(1)

    console.print(f"\n[bold green]✅ Voiceover complete — {len(audio_files)} audio file(s) saved[/]\n")
    return audio_files


def generate_voiceover_from_file(
    script_path: str | Path,
    output_dir: Optional[Path] = None,
    filename_prefix: str = "voiceover",
) -> list[Path]:
    """
    Generate voiceover from a script file.

    Args:
        script_path: Path to a .txt or .md file containing the narration.
        output_dir: Directory to save audio files.
        filename_prefix: Prefix for output filenames.

    Returns:
        List of Paths to the generated MP3 files.
    """
    script_path = Path(script_path)
    if not script_path.exists():
        raise FileNotFoundError(f"Script file not found: {script_path}")

    text = script_path.read_text(encoding="utf-8")
    return generate_voiceover(text, output_dir, filename_prefix)
