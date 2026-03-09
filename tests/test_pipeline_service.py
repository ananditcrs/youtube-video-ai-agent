"""
Tests for the pipeline service.
"""

from ai_video_agent.domain.defaults import DEFAULT_TITLE, DEFAULT_DESCRIPTION, DEFAULT_TAGS
from ai_video_agent.domain.models import JobStatus, GenerateRequest, JobInfo
from ai_video_agent.domain.prompts import DEFAULT_IMAGE_PROMPTS, SCRIPT_SYSTEM_PROMPT


def test_defaults_exist():
    """Verify default constants are properly defined."""
    assert len(DEFAULT_TITLE) > 0
    assert len(DEFAULT_DESCRIPTION) > 0
    assert len(DEFAULT_TAGS) > 0
    assert isinstance(DEFAULT_TAGS, list)


def test_image_prompts_structure():
    """Verify image prompts have the required keys."""
    assert len(DEFAULT_IMAGE_PROMPTS) == 25
    for prompt in DEFAULT_IMAGE_PROMPTS:
        assert "id" in prompt
        assert "prompt" in prompt
        assert len(prompt["prompt"]) > 0


def test_script_system_prompt():
    """Verify the script system prompt is defined."""
    assert len(SCRIPT_SYSTEM_PROMPT) > 100
    assert "voiceover" in SCRIPT_SYSTEM_PROMPT.lower()


def test_job_status_values():
    """Verify job status enum values."""
    assert JobStatus.QUEUED.value == "queued"
    assert JobStatus.RUNNING.value == "running"
    assert JobStatus.COMPLETED.value == "completed"
    assert JobStatus.FAILED.value == "failed"


def test_generate_request_defaults():
    """Verify GenerateRequest has sensible defaults."""
    req = GenerateRequest(topic="Test topic")
    assert req.topic == "Test topic"
    assert req.script is None
    assert req.privacy == "private"
    assert req.skip_upload is True
    assert req.skip_images is False
    assert req.script_minutes == 10


def test_generate_request_with_script():
    """Verify GenerateRequest accepts script text."""
    req = GenerateRequest(script="Hello world, this is a test script.")
    assert req.script == "Hello world, this is a test script."
    assert req.topic is None


def test_job_info_creation():
    """Verify JobInfo model creation."""
    job = JobInfo(
        job_id="abc123",
        status=JobStatus.QUEUED,
        created_at="2026-02-21T10:00:00",
    )
    assert job.job_id == "abc123"
    assert job.status == JobStatus.QUEUED
    assert job.completed_at is None
    assert job.error is None
    assert job.result is None
