"""
Image Service — Generate AI visuals using OpenAI DALL-E 3.
Step 3 of the pipeline.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import httpx
from openai import OpenAI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ai_video_agent.config import openai_cfg, paths
from ai_video_agent.domain.prompts import DEFAULT_IMAGE_PROMPTS

console = Console()


def load_prompts_from_json(json_path: str | Path) -> list[dict[str, str]]:
    """Load custom visual prompts from a JSON file."""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    return data  # expects list of {"id": "...", "prompt": "..."}


def generate_images(
    prompts: Optional[list[dict[str, str]]] = None,
    output_dir: Optional[Path] = None,
    skip_existing: bool = True,
) -> list[Path]:
    """
    Generate images from prompts using OpenAI DALL-E 3.

    Args:
        prompts: List of dicts with 'id' and 'prompt' keys.
                 Defaults to DEFAULT_IMAGE_PROMPTS if None.
        output_dir: Where to save images. Defaults to paths.images.
        skip_existing: If True, skip prompts whose output file already exists.

    Returns:
        List of Paths to generated image files.
    """
    prompts = prompts or DEFAULT_IMAGE_PROMPTS
    output_dir = output_dir or paths.images
    output_dir.mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=openai_cfg.api_key)

    console.print(f"\n[bold cyan]🖼️  AI Image Generator (DALL-E 3)[/]")
    console.print(f"   Prompts   : {len(prompts)}")
    console.print(f"   Model     : {openai_cfg.image_model}")
    console.print(f"   Size      : {openai_cfg.image_size}")
    console.print(f"   Quality   : {openai_cfg.image_quality}")
    console.print(f"   Output    : {output_dir}\n")

    image_files: list[Path] = []
    skipped = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating images…", total=len(prompts))

        for entry in prompts:
            img_id = entry["id"]
            prompt_text = entry["prompt"]
            out_path = output_dir / f"{img_id}.png"

            if skip_existing and out_path.exists():
                console.print(f"   ⏭️  Skipped (exists): {out_path.name}")
                image_files.append(out_path)
                skipped += 1
                progress.advance(task)
                continue

            try:
                response = client.images.generate(
                    model=openai_cfg.image_model,
                    prompt=prompt_text,
                    n=1,
                    size=openai_cfg.image_size,
                    quality=openai_cfg.image_quality,
                    style="vivid",
                )

                image_url = response.data[0].url

                # Download the image
                with httpx.Client(timeout=60) as http_client:
                    img_response = http_client.get(image_url)
                    img_response.raise_for_status()
                    out_path.write_bytes(img_response.content)

                image_files.append(out_path)
                console.print(f"   ✅ Generated: {out_path.name}")

            except Exception as e:
                console.print(f"   [red]❌ Failed: {img_id} — {e}[/]")
                # Create a placeholder so the pipeline doesn't break
                _create_placeholder_image(out_path, img_id)
                image_files.append(out_path)

            progress.advance(task)

            # Rate-limit: DALL-E 3 allows ~7 images/min on paid tier
            time.sleep(10)

    generated = len(image_files) - skipped
    console.print(f"\n[bold green]✅ Image generation complete — {generated} new, {skipped} skipped[/]\n")
    return image_files


def _create_placeholder_image(path: Path, label: str) -> None:
    """Create a dark placeholder image with label text (fallback on DALL-E failure)."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (1920, 1080), color=(20, 20, 40))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except OSError:
            font = ImageFont.load_default()

        text = f"[Placeholder: {label}]"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (1920 - text_w) // 2
        y = (1080 - text_h) // 2
        draw.text((x, y), text, fill=(100, 100, 180), font=font)
        img.save(path)
    except ImportError:
        path.write_bytes(b"")
