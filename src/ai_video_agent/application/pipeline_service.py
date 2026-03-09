"""
Pipeline Service — Main orchestrator for the video generation pipeline.
Coordinates all steps: Script → Voiceover → Images → Video → YouTube.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ai_video_agent.config import paths
from ai_video_agent.domain.defaults import DEFAULT_TITLE, DEFAULT_DESCRIPTION, DEFAULT_TAGS

console = Console()


def run_pipeline(
    script_path: str | Path | None = None,
    topic: str | None = None,
    title: str = DEFAULT_TITLE,
    description: str = DEFAULT_DESCRIPTION,
    tags: list[str] = DEFAULT_TAGS,
    background_music: str | Path | None = None,
    skip_images: bool = False,
    skip_upload: bool = False,
    skip_script: bool = False,
    privacy: str = "private",
    thumbnail: str | Path | None = None,
    prompts_file: str | Path | None = None,
    script_style: str = "informative and engaging",
    script_minutes: int = 10,
) -> dict:
    """
    Run the full AI video agent pipeline.

    Steps:
        1. Generate script from topic using GPT-4o (skipped if script_path provided)
        2. Generate voiceover audio from script text (ElevenLabs)
        3. Generate AI images from visual prompts (DALL-E 3)
        4. Assemble video from images + audio (MoviePy)
        5. Upload to YouTube (YouTube Data API v3)

    Provide either `topic` (AI generates the script) or `script_path` (use existing script).

    Args:
        script_path: Path to an existing voiceover script text file.
        topic: Video topic — GPT-4o will generate the script automatically.
        title: YouTube video title.
        description: YouTube video description.
        tags: YouTube tags/keywords.
        background_music: Optional path to background music file.
        skip_images: If True, skip image generation (use existing images).
        skip_upload: If True, skip YouTube upload (just produce the video).
        skip_script: If True, skip script generation even if topic is provided.
        privacy: YouTube privacy status ("private", "unlisted", "public").
        thumbnail: Optional path to thumbnail image.
        prompts_file: Optional JSON file with custom image prompts.
        script_style: Writing style for script generation (only used with topic).
        script_minutes: Target video length in minutes (only used with topic).

    Returns:
        Dict with pipeline results (paths, video ID, URL, etc.)
    """
    # Validate inputs — need either a topic or a script file
    if not topic and not script_path:
        console.print("[red]❌ Provide either --topic or a script file path.[/]")
        sys.exit(1)

    if script_path:
        script_path = Path(script_path)
        if not script_path.exists():
            console.print(f"[red]❌ Script file not found: {script_path}[/]")
            sys.exit(1)

    paths.ensure_dirs()
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results: dict = {"timestamp": timestamp, "steps": {}}

    # Determine total steps
    has_script_step = bool(topic and not skip_script and not script_path)
    total_steps = 5 if has_script_step else 4
    step_num = 0

    # ── Banner ────────────────────────────────────────────────────────────
    mode = f"Topic: {topic[:60]}" if topic and not script_path else f"Script: {script_path.name}"
    console.print(Panel(
        "[bold white]AI VIDEO AGENT[/]\n"
        f"[dim]{'Topic → Script → ' if has_script_step else ''}Voiceover → Images → Video → YouTube[/]\n\n"
        f"📝 {mode}\n"
        f"🎯 Title:  {title[:60]}…" if len(title) > 60 else
        f"📝 {mode}\n"
        f"🎯 Title:  {title}",
        title="🤖 Pipeline Start",
        border_style="cyan",
    ))

    # ══════════════════════════════════════════════════════════════════════
    # STEP 1: SCRIPT GENERATION (from topic)
    # ══════════════════════════════════════════════════════════════════════
    if has_script_step:
        step_num += 1
        console.print(Panel(f"[bold]STEP {step_num}/{total_steps} — Script Generation (GPT-4o)[/]", border_style="blue"))

        from ai_video_agent.application.script_service import generate_script

        script_path = generate_script(
            topic=topic,
            style=script_style,
            target_minutes=script_minutes,
        )

        results["steps"]["script"] = {
            "status": "success",
            "path": str(script_path),
            "topic": topic,
        }
    elif topic and script_path:
        console.print(f"   ℹ️  Script file provided — skipping script generation (topic: {topic})")
        results["steps"]["script"] = {"status": "skipped", "reason": "script_path provided"}

    # ══════════════════════════════════════════════════════════════════════
    # STEP 2: VOICEOVER GENERATION
    # ══════════════════════════════════════════════════════════════════════
    step_num += 1
    console.print(Panel(f"[bold]STEP {step_num}/{total_steps} — Voiceover Generation (ElevenLabs)[/]", border_style="blue"))

    from ai_video_agent.application.voiceover_service import generate_voiceover_from_file

    audio_files = generate_voiceover_from_file(
        script_path=script_path,
        output_dir=paths.audio,
        filename_prefix="voiceover",
    )

    results["steps"]["voiceover"] = {
        "status": "success",
        "files": [str(f) for f in audio_files],
        "count": len(audio_files),
    }

    # ══════════════════════════════════════════════════════════════════════
    # STEP 3: IMAGE GENERATION
    # ══════════════════════════════════════════════════════════════════════
    step_num += 1
    console.print(Panel(f"[bold]STEP {step_num}/{total_steps} — Image Generation (DALL-E 3)[/]", border_style="blue"))

    if skip_images:
        console.print("   ⏭️  Skipping image generation (--skip-images flag)")
        existing_images = sorted(paths.images.glob("*.png"))
        if not existing_images:
            existing_images = sorted(paths.images.glob("*.jpg"))
        if not existing_images:
            console.print("[red]❌ No existing images found in output/images/. Remove --skip-images flag.[/]")
            sys.exit(1)
        console.print(f"   Using {len(existing_images)} existing image(s)")
        results["steps"]["images"] = {
            "status": "skipped",
            "count": len(existing_images),
        }
    else:
        from ai_video_agent.application.image_service import generate_images, load_prompts_from_json

        custom_prompts = None
        if prompts_file:
            custom_prompts = load_prompts_from_json(prompts_file)

        image_files = generate_images(
            prompts=custom_prompts,
            output_dir=paths.images,
            skip_existing=True,
        )

        results["steps"]["images"] = {
            "status": "success",
            "files": [str(f) for f in image_files],
            "count": len(image_files),
        }

    # ══════════════════════════════════════════════════════════════════════
    # STEP 4: VIDEO ASSEMBLY
    # ══════════════════════════════════════════════════════════════════════
    step_num += 1
    console.print(Panel(f"[bold]STEP {step_num}/{total_steps} — Video Assembly (MoviePy)[/]", border_style="blue"))

    from ai_video_agent.application.video_service import assemble_video

    video_filename = f"ai_trends_2026_{timestamp}.mp4"
    output_video_path = paths.video / video_filename

    bg_music = Path(background_music) if background_music else None

    video_path = assemble_video(
        audio_dir=paths.audio,
        image_dir=paths.images,
        output_path=output_video_path,
        background_music_path=bg_music,
        title_text=title,
    )

    results["steps"]["video"] = {
        "status": "success",
        "path": str(video_path),
        "size_mb": round(video_path.stat().st_size / (1024 * 1024), 1),
    }

    # ══════════════════════════════════════════════════════════════════════
    # STEP 5: YOUTUBE UPLOAD
    # ══════════════════════════════════════════════════════════════════════
    step_num += 1
    console.print(Panel(f"[bold]STEP {step_num}/{total_steps} — YouTube Upload[/]", border_style="blue"))

    if skip_upload:
        console.print("   ⏭️  Skipping YouTube upload (--skip-upload flag)")
        console.print(f"   📁 Video saved at: {video_path}")
        results["steps"]["youtube"] = {"status": "skipped"}
    else:
        from ai_video_agent.application.youtube_service import upload_video

        thumb = Path(thumbnail) if thumbnail else None
        if thumb is None:
            auto_thumb = paths.thumbnails / "thumbnail.png"
            if auto_thumb.exists():
                thumb = auto_thumb

        upload_result = upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy,
            thumbnail_path=thumb,
        )

        results["steps"]["youtube"] = {
            "status": "success",
            **upload_result,
        }

    # ══════════════════════════════════════════════════════════════════════
    # PIPELINE COMPLETE
    # ══════════════════════════════════════════════════════════════════════
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    results["total_time_seconds"] = round(elapsed, 1)

    # Save run log
    log_path = paths.output / f"run_log_{timestamp}.json"
    log_path.write_text(json.dumps(results, indent=2))

    # Summary table
    table = Table(title="Pipeline Summary", border_style="green")
    table.add_column("Step", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    for step_name, step_data in results["steps"].items():
        status = step_data.get("status", "unknown")
        status_icon = "✅" if status == "success" else "⏭️" if status == "skipped" else "❌"
        details = ""
        if step_name == "script":
            details = step_data.get("topic", step_data.get("reason", "—"))
        elif step_name == "voiceover":
            details = f"{step_data.get('count', 0)} audio file(s)"
        elif step_name == "images":
            details = f"{step_data.get('count', 0)} image(s)"
        elif step_name == "video":
            details = f"{step_data.get('size_mb', 0)} MB"
        elif step_name == "youtube":
            details = step_data.get("video_url", "—")
        table.add_row(step_name.title(), f"{status_icon} {status}", details)

    console.print("\n")
    console.print(table)
    console.print(f"\n⏱️  Total time: {minutes}m {seconds}s")
    console.print(f"📋 Run log: {log_path}\n")

    if "youtube" in results["steps"] and results["steps"]["youtube"].get("video_url"):
        console.print(Panel(
            f"[bold green]🎉 Your video is live![/]\n\n"
            f"[bold]{results['steps']['youtube']['video_url']}[/]",
            border_style="green",
        ))

    return results
