"""Safety validators and guardrails."""

import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

class ValidationError(Exception):
    """Validation error."""
    pass

def validate_video_file(file_path: Path) -> None:
    """Validate a video file exists and has supported format."""
    if not file_path.exists():
        raise ValidationError(f"Video file not found: {file_path}")
    
    if not file_path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")
    
    ext = file_path.suffix.lower().lstrip('.')
    supported = ['mp4', 'mpeg', 'mov', 'avi', 'webm', 'flv', 'mpg', '3gpp', 'wmv']
    if ext not in supported:
        raise ValidationError(f"Unsupported video format: {ext}. Supported: {', '.join(supported)}")
    
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > 2000:
        raise ValidationError(f"Video file too large: {size_mb:.1f}MB. Maximum: 2000MB")

def validate_youtube_url(url: str) -> bool:
    """Validate if a URL is a valid YouTube URL."""
    youtube_patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/embed/[\w-]+',
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns)

def validate_api_key(api_key: str) -> None:
    """Validate API key format."""
    if not api_key or not api_key.strip():
        raise ValidationError("API key is required. Set GOOGLE_API_KEY in .env file")
    
    if len(api_key) < 10:
        raise ValidationError("API key appears to be invalid (too short)")

def check_file_size_for_inline(file_path: Path, threshold_mb: int = 20) -> bool:
    """Check if file size is suitable for inline upload."""
    size_mb = file_path.stat().st_size / (1024 * 1024)
    return size_mb < threshold_mb

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to remove problematic characters."""
    sanitized = re.sub(r'[^\w\s\-\.]', '_', filename)
    sanitized = re.sub(r'[\s]+', '_', sanitized)
    return sanitized.strip('_')

def validate_report_path(report_path: Path) -> None:
    """Validate a report file path."""
    if not report_path.exists():
        raise ValidationError(f"Report file not found: {report_path}")
    
    if not report_path.is_file():
        raise ValidationError(f"Path is not a file: {report_path}")
    
    if report_path.suffix.lower() != '.json':
        raise ValidationError(f"Report must be a JSON file, got: {report_path.suffix}")
