"""Utility functions."""

import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime
import re

def generate_video_id(source: str) -> str:
    """Generate a unique video ID from a file path, URL, or free-form text."""
    if source.startswith('http'):
        hash_base = source
    else:
        path = Path(source)
        try:
            if path.exists():
                hash_base = f"{path.name}_{path.stat().st_mtime}"
            else:
                hash_base = source
        except (OSError, ValueError):
            hash_base = source

    hash_obj = hashlib.md5(hash_base.encode("utf-8"))
    return hash_obj.hexdigest()[:12]

def parse_timestamp(timestamp: str) -> float:
    """Parse timestamp string (MM:SS or HH:MM:SS) to seconds."""
    parts = timestamp.split(':')
    
    try:
        if len(parts) == 2:
            minutes, seconds = map(float, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            return float(timestamp)
    except ValueError:
        return 0.0

def format_timestamp(seconds: float) -> str:
    """Format seconds to MM:SS string."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def extract_video_id_from_youtube(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([\w-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def get_run_id() -> str:
    """Generate a unique run ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
