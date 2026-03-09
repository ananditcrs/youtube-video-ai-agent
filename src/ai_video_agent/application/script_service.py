"""
Script Service — Generate voiceover scripts from topics using GPT-4o.
Step 1 of the pipeline (when --topic is used).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from openai import OpenAI
from rich.console import Console

from ai_video_agent.config import openai_cfg, paths
from ai_video_agent.domain.prompts import SCRIPT_SYSTEM_PROMPT

console = Console()


def generate_script(
    topic: str,
    style: str = "informative and engaging",
    target_minutes: int = 10,
    output_path: str | Path | None = None,
    model: str = "gpt-4o",
) -> Path:
    """
    Generate a voiceover script from a topic using GPT-4o.

    Args:
        topic: The video topic or a brief description of what the video should cover.
        style: Writing style (e.g., "informative", "casual", "dramatic", "tutorial").
        target_minutes: Target video length in minutes.
        output_path: Where to save the script. Defaults to output/scripts/script_{timestamp}.txt
        model: OpenAI model to use.

    Returns:
        Path to the generated script file.
    """
    target_words = target_minutes * 150  # ~150 words per minute of speech

    console.print(f"[cyan]📝 Generating script for:[/] {topic}")
    console.print(f"   Style: {style} | Target: ~{target_minutes} min ({target_words} words)")

    client = OpenAI(api_key=openai_cfg.api_key)

    user_prompt = (
        f"Write a voiceover script about: {topic}\n\n"
        f"Style: {style}\n"
        f"Target length: ~{target_words} words ({target_minutes} minutes when read aloud)\n"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
        max_tokens=4000,
    )

    script_text = response.choices[0].message.content.strip()
    word_count = len(script_text.split())
    est_minutes = round(word_count / 150, 1)

    console.print(f"   [green]✅ Generated {word_count} words (~{est_minutes} min read time)[/]")

    # Save to file
    if output_path is None:
        scripts_dir = paths.output / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = scripts_dir / f"script_{timestamp}.txt"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(script_text, encoding="utf-8")
    console.print(f"   📁 Saved to: {output_path}")

    return output_path
