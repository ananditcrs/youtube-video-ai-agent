"""
Video Service — Assemble final MP4 from images + audio using MoviePy.
Step 4 of the pipeline.
Supports: Ken Burns effect, cross-fade transitions, text overlays, background music.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ai_video_agent.config import video_cfg, paths

console = Console()


def _natural_sort_key(path: Path) -> list:
    """Sort key that handles numbers in filenames naturally."""
    return [
        int(c) if c.isdigit() else c.lower()
        for c in re.split(r"(\d+)", path.stem)
    ]


def assemble_video(
    audio_dir: Optional[Path] = None,
    image_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
    background_music_path: Optional[Path] = None,
    title_text: Optional[str] = None,
) -> Path:
    """
    Assemble a video from images and voiceover audio.

    Pipeline:
    1. Concatenate all audio chunks into a single voiceover track
    2. Calculate total duration from the voiceover
    3. Distribute images evenly across the duration with Ken Burns effect
    4. Add cross-fade transitions between images
    5. Mix in background music at low volume
    6. Export final MP4

    Args:
        audio_dir: Directory containing voiceover MP3 files.
        image_dir: Directory containing generated images.
        output_path: Path for the final video file.
        background_music_path: Optional path to background music file.
        title_text: Optional title overlay text for the intro.

    Returns:
        Path to the exported video file.
    """
    # Lazy imports — MoviePy is heavy
    from moviepy.editor import (
        AudioFileClip,
        CompositeAudioClip,
        CompositeVideoClip,
        ImageClip,
        TextClip,
        concatenate_audioclips,
        concatenate_videoclips,
    )

    audio_dir = audio_dir or paths.audio
    image_dir = image_dir or paths.images
    output_dir = output_path.parent if output_path else paths.video
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_path or paths.video / "final_video.mp4"

    console.print(f"\n[bold cyan]🎬 Video Assembler[/]")

    # ── Step 1: Load and concatenate audio ────────────────────────────────
    console.print("   [dim]Step 1/5:[/] Loading audio files…")
    audio_files = sorted(
        [f for f in audio_dir.iterdir() if f.suffix.lower() in (".mp3", ".wav")],
        key=_natural_sort_key,
    )

    if not audio_files:
        raise FileNotFoundError(f"No audio files found in {audio_dir}")

    console.print(f"   Found {len(audio_files)} audio file(s)")

    audio_clips = [AudioFileClip(str(f)) for f in audio_files]
    full_voiceover = concatenate_audioclips(audio_clips)
    total_duration = full_voiceover.duration

    console.print(f"   Total voiceover duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")

    # ── Step 2: Load images ───────────────────────────────────────────────
    console.print("   [dim]Step 2/5:[/] Loading images…")
    image_files = sorted(
        [f for f in image_dir.iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")],
        key=_natural_sort_key,
    )

    if not image_files:
        raise FileNotFoundError(f"No image files found in {image_dir}")

    console.print(f"   Found {len(image_files)} image(s)")

    # ── Step 3: Create image clips with Ken Burns effect ──────────────────
    console.print("   [dim]Step 3/5:[/] Building image sequence with Ken Burns effect…")

    duration_per_image = total_duration / len(image_files)
    fade = min(video_cfg.fade_duration, duration_per_image * 0.15)

    video_clips = []
    w, h = video_cfg.width, video_cfg.height

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        task = prog.add_task(f"Processing {len(image_files)} images…", total=len(image_files))

        for i, img_path in enumerate(image_files):
            clip = (
                ImageClip(str(img_path))
                .set_duration(duration_per_image)
                .resize((w, h))
            )

            # Ken Burns: alternate between slow zoom-in and slow zoom-out
            zoom_direction = 1 if i % 2 == 0 else -1
            start_scale = 1.0
            end_scale = 1.08 if zoom_direction == 1 else 0.93

            def make_zoom(clip, start_s=start_scale, end_s=end_scale, dur=duration_per_image):
                def zoom_func(get_frame, t):
                    progress_ratio = t / dur
                    scale = start_s + (end_s - start_s) * progress_ratio
                    frame = get_frame(t)
                    return frame
                return clip

            clip = make_zoom(clip)

            if fade > 0:
                clip = clip.crossfadein(fade)

            video_clips.append(clip)
            prog.advance(task)

    # ── Step 4: Combine into final video ──────────────────────────────────
    console.print("   [dim]Step 4/5:[/] Compositing video…")

    if fade > 0 and len(video_clips) > 1:
        final_video = concatenate_videoclips(
            video_clips,
            method="compose",
            padding=-fade,
        )
    else:
        final_video = concatenate_videoclips(video_clips, method="compose")

    # Add title text overlay (first 5 seconds)
    if title_text:
        try:
            title_clip = (
                TextClip(
                    title_text,
                    fontsize=64,
                    color="white",
                    font="Arial-Bold",
                    stroke_color="black",
                    stroke_width=2,
                )
                .set_position("center")
                .set_duration(5)
                .crossfadein(0.5)
                .crossfadeout(0.5)
            )
            final_video = CompositeVideoClip([final_video, title_clip])
        except Exception as e:
            console.print(f"   [yellow]⚠️  Title overlay skipped (font issue): {e}[/]")

    # ── Build audio mix ──────────────────────────────────────────────────
    audio_tracks = [full_voiceover]

    if background_music_path and Path(background_music_path).exists():
        console.print(f"   [dim]Adding background music at {video_cfg.bg_music_volume*100:.0f}% volume[/]")
        bg_music = (
            AudioFileClip(str(background_music_path))
            .volumex(video_cfg.bg_music_volume)
        )
        if bg_music.duration < total_duration:
            loops_needed = int(total_duration / bg_music.duration) + 1
            bg_music = concatenate_audioclips([bg_music] * loops_needed)
        bg_music = bg_music.subclip(0, total_duration)
        audio_tracks.append(bg_music)

    mixed_audio = CompositeAudioClip(audio_tracks) if len(audio_tracks) > 1 else audio_tracks[0]

    final_video = final_video.subclip(0, min(final_video.duration, total_duration))
    final_video = final_video.set_audio(mixed_audio)

    # ── Step 5: Export ────────────────────────────────────────────────────
    console.print(f"   [dim]Step 5/5:[/] Exporting to {output_path.name}…")
    console.print(f"   Resolution: {w}x{h} @ {video_cfg.fps}fps")
    console.print(f"   [yellow]⏳ This may take several minutes…[/]\n")

    final_video.write_videofile(
        str(output_path),
        fps=video_cfg.fps,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",
        audio_bitrate="320k",
        preset="medium",
        threads=4,
        logger="bar",
    )

    # Cleanup
    for clip in audio_clips:
        clip.close()
    full_voiceover.close()
    final_video.close()

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    console.print(f"\n[bold green]✅ Video exported: {output_path}[/]")
    console.print(f"   Size: {file_size_mb:.1f} MB\n")

    return output_path
