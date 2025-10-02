"""Configuration and settings management."""

import os
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class GeminiConfig(BaseModel):
    """Gemini API configuration."""
    model: str = Field(default="gemini-2.0-flash-exp")
    max_retries: int = Field(default=3)
    timeout: int = Field(default=120)
    file_api_threshold_mb: int = Field(default=20)

class VideoConfig(BaseModel):
    """Video processing configuration."""
    default_fps: int = Field(default=1)
    max_duration_seconds: int = Field(default=3600)
    supported_formats: list[str] = Field(default_factory=lambda: ["mp4", "mpeg", "mov", "avi", "webm"])

class PromptsConfig(BaseModel):
    """Prompt generation configuration."""
    include_timestamps: bool = Field(default=True)
    include_camera_details: bool = Field(default=True)
    include_lighting: bool = Field(default=True)
    include_style: bool = Field(default=True)
    max_prompt_length: int = Field(default=500)

class PipelineConfig(BaseModel):
    """Pipeline configuration."""
    checkpoint_enabled: bool = Field(default=True)
    retry_on_failure: bool = Field(default=True)
    max_retries: int = Field(default=3)

class Settings(BaseModel):
    """Application settings."""
    google_api_key: str = Field(default="")
    assets_dir: Path = Field(default=Path("assets"))
    inputs_dir: Path = Field(default=Path("assets/inputs"))
    reports_dir: Path = Field(default=Path("assets/reports"))
    prompts_dir: Path = Field(default=Path("assets/prompts"))
    runs_dir: Path = Field(default=Path("assets/runs"))
    logs_dir: Path = Field(default=Path("assets/logs"))
    log_level: str = Field(default="INFO")
    
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from environment and config file."""
        if config_path is None:
            config_path = Path("config.yaml")
        
        config_data = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        
        env_google_api_key = os.getenv("GOOGLE_API_KEY", "")
        if env_google_api_key:
            config_data["google_api_key"] = env_google_api_key
        
        env_log_level = os.getenv("LOG_LEVEL")
        if env_log_level:
            config_data["log_level"] = env_log_level
        
        env_assets_dir = os.getenv("ASSETS_DIR")
        if env_assets_dir:
            config_data["assets_dir"] = env_assets_dir
        
        env_model = os.getenv("MODEL_GEMINI")
        if env_model:
            if "gemini" not in config_data:
                config_data["gemini"] = {}
            config_data["gemini"]["model"] = env_model
        
        return cls(**config_data)
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        for dir_attr in ["assets_dir", "inputs_dir", "reports_dir", "prompts_dir", "runs_dir", "logs_dir"]:
            dir_path = getattr(self, dir_attr)
            dir_path.mkdir(parents=True, exist_ok=True)

settings = Settings.load()
settings.ensure_directories()
