"""Domain models for AI video analysis and prompt generation."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class CameraMovement(str, Enum):
    """Camera movement types."""
    STATIC = "static"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    TRACKING = "tracking"
    ORBIT = "orbit"
    HANDHELD = "handheld"
    AERIAL = "aerial"
    DOLLY = "dolly"
    CRANE = "crane"

class ShotType(str, Enum):
    """Shot types."""
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    OVER_SHOULDER = "over_shoulder"
    POV = "pov"
    TWO_SHOT = "two_shot"
    ESTABLISHING = "establishing"

class Entity(BaseModel):
    """An entity in the video (person, object, etc.)."""
    name: str
    type: str = Field(description="Type: person, object, animal, etc.")
    description: Optional[str] = None
    appearance: Optional[str] = Field(default=None, description="Visual appearance details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Woman",
                "type": "person",
                "description": "Main character",
                "appearance": "Long blonde hair, white t-shirt, blue jeans"
            }
        }

class Shot(BaseModel):
    """A single shot within a scene."""
    shot_index: int
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    duration: float = Field(description="Duration in seconds")
    description: str
    action: str = Field(description="What's happening in this shot")
    shot_type: Optional[str] = None
    camera_movement: Optional[str] = None
    camera_description: Optional[str] = None
    entities: list[Entity] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "shot_index": 1,
                "start_time": 0.0,
                "end_time": 5.0,
                "duration": 5.0,
                "description": "Woman enters kitchen",
                "action": "Walking from doorway to counter",
                "shot_type": "medium",
                "camera_movement": "tracking",
                "camera_description": "Camera follows woman from behind",
                "entities": []
            }
        }

class Scene(BaseModel):
    """A scene in the video."""
    scene_index: int
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
    duration: float = Field(description="Duration in seconds")
    location: str = Field(description="Where the scene takes place")
    description: str
    mood: Optional[str] = None
    lighting: Optional[str] = None
    color_palette: Optional[str] = None
    style: Optional[str] = None
    shots: list[Shot] = Field(default_factory=list)
    key_entities: list[Entity] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "scene_index": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "duration": 15.0,
                "location": "Modern kitchen",
                "description": "Woman prepares morning coffee",
                "mood": "Calm, peaceful morning",
                "lighting": "Soft morning light through windows",
                "color_palette": "Warm tones, bright whites",
                "style": "Cinematic, realistic",
                "shots": [],
                "key_entities": []
            }
        }

class VideoReport(BaseModel):
    """Complete analysis report of a video."""
    video_id: str = Field(description="Unique identifier for the video")
    source: str = Field(description="Source file path or URL")
    duration: float = Field(description="Total duration in seconds")
    fps: Optional[float] = None
    resolution: Optional[str] = None
    title: Optional[str] = None
    summary: str = Field(description="Overall summary of the video")
    overall_style: Optional[str] = None
    overall_mood: Optional[str] = None
    color_grading: Optional[str] = None
    scenes: list[Scene] = Field(default_factory=list)
    main_entities: list[Entity] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "sample_video_001",
                "source": "assets/inputs/sample.mp4",
                "duration": 30.0,
                "fps": 30.0,
                "resolution": "1920x1080",
                "title": "Coffee Commercial",
                "summary": "A morning coffee commercial showing a woman preparing coffee",
                "overall_style": "Cinematic, commercial",
                "overall_mood": "Warm, inviting",
                "color_grading": "Warm tones with high contrast",
                "scenes": [],
                "main_entities": [],
                "created_at": "2024-01-01T12:00:00"
            }
        }

class PromptType(str, Enum):
    """Type of prompt."""
    IMAGE_TO_VIDEO = "image_to_video"
    TEXT_TO_VIDEO = "text_to_video"
    TEXT_TO_IMAGE = "text_to_image"

class PromptSpec(BaseModel):
    """A generated prompt for AI generation."""
    prompt_type: PromptType
    text: str = Field(description="The actual prompt text")
    subject: str = Field(description="Main subject of the prompt")
    action: str = Field(description="Action being performed")
    scene: str = Field(description="Scene/background description")
    camera: Optional[str] = None
    lighting: Optional[str] = None
    style: Optional[str] = None
    negative_prompt: Optional[str] = None
    reference_images: list[str] = Field(default_factory=list, description="Paths to reference images")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_type": "text_to_image",
                "text": "A woman with long blonde hair in a modern kitchen, morning light",
                "subject": "Woman with long blonde hair",
                "action": "Standing in kitchen",
                "scene": "Modern kitchen with white counters",
                "camera": "Medium shot",
                "lighting": "Soft morning light through windows",
                "style": "Cinematic, realistic",
                "negative_prompt": "blur, distortion, low quality",
                "reference_images": []
            }
        }

class PromptBundle(BaseModel):
    """A bundle of prompts for a scene."""
    scene_index: int
    start_time: float
    end_time: float
    duration: float
    image_prompts: list[PromptSpec] = Field(default_factory=list, description="Text-to-image prompts")
    video_prompts: list[PromptSpec] = Field(default_factory=list, description="Image-to-video or text-to-video prompts")
    shot_descriptions: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "scene_index": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "duration": 15.0,
                "image_prompts": [],
                "video_prompts": [],
                "shot_descriptions": ["Woman enters kitchen", "Close-up of coffee mug"],
                "notes": "Focus on warm morning atmosphere",
                "created_at": "2024-01-01T12:00:00"
            }
        }
