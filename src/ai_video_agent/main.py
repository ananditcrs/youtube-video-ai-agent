"""
AI Video Agent — CLI Entry Point
Topic (or Script) → Voiceover → Images → Video → YouTube in one command.

Usage:
    python -m ai_video_agent --topic "Top 5 AI Agents in 2026"
    python -m ai_video_agent script.txt
    python -m ai_video_agent --topic "How Agentic AI Works" --style tutorial --minutes 12
"""

from __future__ import annotations

import argparse

from ai_video_agent.domain.defaults import DEFAULT_TITLE, DEFAULT_DESCRIPTION, DEFAULT_TAGS
from ai_video_agent.application.pipeline_service import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="🤖 AI Video Agent — Topic (or Script) to YouTube in one command",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # From a TOPIC — AI generates the script, then full pipeline
  python -m ai_video_agent --topic "Top 5 AI Agents Replacing SaaS in 2026"

  # Topic with custom style and length
  python -m ai_video_agent --topic "How Agentic AI Works" --style "tutorial" --minutes 12

  # From an existing SCRIPT file (skips script generation)
  python -m ai_video_agent script.txt

  # Skip image generation (use existing images in output/images/)
  python -m ai_video_agent script.txt --skip-images

  # Generate video without uploading to YouTube
  python -m ai_video_agent --topic "AI in 2026" --skip-upload

  # Custom title and public upload
  python -m ai_video_agent --topic "Future of AI" --title "My AI Video" --privacy public

  # With background music and custom thumbnail
  python -m ai_video_agent script.txt --music bg_track.mp3 --thumbnail thumb.png

  # Use custom image prompts from a JSON file
  python -m ai_video_agent script.txt --prompts custom_prompts.json
        """,
    )

    parser.add_argument(
        "script",
        nargs="?",
        default=None,
        help="Path to the voiceover script text file (.txt or .md). Optional if --topic is used.",
    )
    parser.add_argument(
        "--topic",
        default=None,
        help="Video topic — GPT-4o will generate the voiceover script automatically",
    )
    parser.add_argument(
        "--style",
        default="informative and engaging",
        help="Writing style for AI script generation (default: informative and engaging)",
    )
    parser.add_argument(
        "--minutes",
        type=int,
        default=10,
        help="Target video length in minutes for AI script generation (default: 10)",
    )
    parser.add_argument(
        "--title", "-t",
        default=DEFAULT_TITLE,
        help="YouTube video title (default: AI Trends 2026 title)",
    )
    parser.add_argument(
        "--description", "-d",
        default=DEFAULT_DESCRIPTION,
        help="YouTube video description",
    )
    parser.add_argument(
        "--tags",
        nargs="*",
        default=DEFAULT_TAGS,
        help="YouTube tags/keywords",
    )
    parser.add_argument(
        "--music", "-m",
        default=None,
        help="Path to background music file (MP3/WAV)",
    )
    parser.add_argument(
        "--thumbnail",
        default=None,
        help="Path to custom thumbnail image",
    )
    parser.add_argument(
        "--prompts",
        default=None,
        help="JSON file with custom image prompts [{id, prompt}, ...]",
    )
    parser.add_argument(
        "--privacy",
        choices=["private", "unlisted", "public"],
        default="private",
        help="YouTube privacy status (default: private)",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip image generation (use existing images in output/images/)",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip YouTube upload (just generate the video file)",
    )

    args = parser.parse_args()

    if not args.script and not args.topic:
        parser.error("Provide either a script file path or --topic \"Your video topic\"")

    run_pipeline(
        script_path=args.script,
        topic=args.topic,
        title=args.title,
        description=args.description,
        tags=args.tags,
        background_music=args.music,
        skip_images=args.skip_images,
        skip_upload=args.skip_upload,
        privacy=args.privacy,
        thumbnail=args.thumbnail,
        prompts_file=args.prompts,
        script_style=args.style,
        script_minutes=args.minutes,
    )


if __name__ == "__main__":
    main()
