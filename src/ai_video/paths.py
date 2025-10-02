"""Path management for assets and artifacts."""

from pathlib import Path
from typing import Optional
from datetime import datetime
from .settings import settings

class PathBuilder:
    """Build paths for various artifacts."""
    
    def __init__(self, assets_dir: Optional[Path] = None):
        self.assets_dir = assets_dir or settings.assets_dir
        self.inputs_dir = settings.inputs_dir
        self.reports_dir = settings.reports_dir
        self.prompts_dir = settings.prompts_dir
        self.runs_dir = settings.runs_dir
        self.logs_dir = settings.logs_dir
    
    def get_report_path(self, video_id: str) -> Path:
        """Get path for a video report."""
        return self.reports_dir / f"{video_id}_report.json"
    
    def get_scene_prompt_path(self, video_id: str, scene_index: int) -> Path:
        """Get path for a scene's prompt bundle."""
        scene_dir = self.prompts_dir / video_id
        scene_dir.mkdir(parents=True, exist_ok=True)
        return scene_dir / f"scene_{scene_index:03d}.json"
    
    def get_prompts_export_path(self, video_id: str, format: str = "md") -> Path:
        """Get path for exported prompts."""
        return self.prompts_dir / video_id / f"prompts.{format}"
    
    def get_run_manifest_path(self, run_id: Optional[str] = None) -> Path:
        """Get path for a run manifest."""
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.runs_dir / f"run_{run_id}.json"
    
    def get_log_path(self, log_name: str) -> Path:
        """Get path for a log file."""
        date_str = datetime.now().strftime("%Y%m%d")
        return self.logs_dir / f"{log_name}_{date_str}.log"
    
    def get_thumbnail_path(self, video_id: str, scene_index: int, frame_type: str = "first") -> Path:
        """Get path for a scene thumbnail."""
        thumbnails_dir = self.reports_dir / video_id / "thumbnails"
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        return thumbnails_dir / f"scene_{scene_index:03d}_{frame_type}.jpg"
    
    def get_video_prompts_dir(self, video_id: str) -> Path:
        """Get directory for all prompts of a video."""
        prompts_dir = self.prompts_dir / video_id
        prompts_dir.mkdir(parents=True, exist_ok=True)
        return prompts_dir
    
    def get_run_dir(self, run_id: str) -> Path:
        """Get directory for a specific run."""
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

path_builder = PathBuilder()
