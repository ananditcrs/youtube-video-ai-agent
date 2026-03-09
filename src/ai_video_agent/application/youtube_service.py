"""
YouTube Service — Upload videos to YouTube using the YouTube Data API v3.
Step 5 of the pipeline.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from rich.console import Console

from ai_video_agent.config import youtube_cfg, paths

console = Console()

# YouTube API constants
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
MAX_RETRIES = 5


def _get_authenticated_service():
    """
    Authenticate with YouTube Data API v3 using OAuth2.

    First run: opens a browser for Google OAuth consent.
    Subsequent runs: uses saved token from youtube_token.json.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token_path = Path(youtube_cfg.token_file)
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), [YOUTUBE_UPLOAD_SCOPE])

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            console.print("   [dim]Refreshing YouTube token…[/]")
            creds.refresh(Request())
        else:
            client_secret = Path(youtube_cfg.client_secret_file)
            if not client_secret.exists():
                raise FileNotFoundError(
                    f"YouTube client_secret.json not found at: {client_secret.resolve()}\n"
                    "  → Download it from Google Cloud Console:\n"
                    "    https://console.cloud.google.com/apis/credentials\n"
                    "  → Create OAuth 2.0 Client ID (Desktop App)\n"
                    "  → Save the JSON file as 'client_secret.json' in the project root"
                )

            console.print("\n   [bold yellow]🔐 YouTube OAuth: A browser window will open.[/]")
            console.print("   [yellow]   Sign in with your Google account and grant access.[/]\n")

            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secret),
                scopes=[YOUTUBE_UPLOAD_SCOPE],
            )
            creds = flow.run_local_server(port=8090)

        token_path.write_text(creds.to_json())
        console.print("   ✅ YouTube token saved for future uploads")

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)


def upload_video(
    video_path: str | Path,
    title: str,
    description: str,
    tags: Optional[list[str]] = None,
    category_id: Optional[str] = None,
    privacy_status: Optional[str] = None,
    thumbnail_path: Optional[str | Path] = None,
    playlist_id: Optional[str] = None,
) -> dict:
    """
    Upload a video to YouTube.

    Args:
        video_path: Path to the MP4 video file.
        title: Video title (max 100 chars).
        description: Video description (max 5000 chars).
        tags: List of tags/keywords.
        category_id: YouTube category ID (28 = Science & Tech).
        privacy_status: "private", "unlisted", or "public".
        thumbnail_path: Optional custom thumbnail image path.
        playlist_id: Optional playlist ID to add the video to.

    Returns:
        Dict with upload result including video ID and URL.
    """
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    category_id = category_id or youtube_cfg.category_id
    privacy_status = privacy_status or youtube_cfg.privacy
    tags = tags or []

    console.print(f"\n[bold cyan]📤 YouTube Uploader[/]")
    console.print(f"   File     : {video_path.name} ({file_size_mb:.1f} MB)")
    console.print(f"   Title    : {title[:80]}…" if len(title) > 80 else f"   Title    : {title}")
    console.print(f"   Privacy  : {privacy_status}")
    console.print(f"   Category : {category_id}")
    console.print(f"   Tags     : {len(tags)} tag(s)\n")

    console.print("   [dim]Authenticating with YouTube…[/]")
    youtube = _get_authenticated_service()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category_id,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=50 * 1024 * 1024,
    )

    console.print("   [yellow]⏳ Uploading… (this may take several minutes for large files)[/]")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    retry_count = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress_pct = int(status.progress() * 100)
                console.print(f"   📊 Upload progress: {progress_pct}%")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES and retry_count < MAX_RETRIES:
                retry_count += 1
                wait_time = 2 ** retry_count
                console.print(f"   [yellow]⚠️  Retrying in {wait_time}s (attempt {retry_count}/{MAX_RETRIES})…[/]")
                time.sleep(wait_time)
            else:
                raise

    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    console.print(f"\n   ✅ Upload complete!")
    console.print(f"   📺 Video ID  : {video_id}")
    console.print(f"   🔗 Video URL : {video_url}")

    # Set custom thumbnail
    if thumbnail_path:
        thumbnail_path = Path(thumbnail_path)
        if thumbnail_path.exists():
            try:
                console.print(f"   [dim]Setting custom thumbnail…[/]")
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png"),
                ).execute()
                console.print("   ✅ Custom thumbnail set")
            except Exception as e:
                console.print(f"   [yellow]⚠️  Thumbnail failed (may need verified account): {e}[/]")
        else:
            console.print(f"   [yellow]⚠️  Thumbnail file not found: {thumbnail_path}[/]")

    # Add to playlist
    if playlist_id:
        try:
            console.print(f"   [dim]Adding to playlist {playlist_id}…[/]")
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    }
                },
            ).execute()
            console.print("   ✅ Added to playlist")
        except Exception as e:
            console.print(f"   [yellow]⚠️  Playlist add failed: {e}[/]")

    result = {
        "video_id": video_id,
        "video_url": video_url,
        "title": title,
        "privacy_status": privacy_status,
        "file_size_mb": round(file_size_mb, 1),
    }

    console.print(f"\n[bold green]✅ YouTube upload complete![/]")
    console.print(f"   [bold]{video_url}[/]\n")

    return result
