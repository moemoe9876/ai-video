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
    # CRITICAL FIELDS - Blueprint demands these, but Optional for validation stability
    camera_position: Optional[str] = Field(default=None, description="Exact camera position relative to subject - CRITICAL")
    camera_angle_degrees: Optional[str] = Field(default=None, description="Camera angle in degrees - CRITICAL")
    camera_distance_meters: Optional[str] = Field(default=None, description="Distance from subject in meters - CRITICAL")
    camera_height_meters: Optional[str] = Field(default=None, description="Height of camera from ground - CRITICAL")
    subject_position_frame: Optional[str] = Field(default=None, description="Subject position in frame (thirds, etc.) - CRITICAL")
    spatial_relationships: Optional[str] = Field(default=None, description="3D spatial relationships - CRITICAL")
    
    # OPTIONAL FIELDS
    camera_movement_trajectory: Optional[str] = Field(default=None, description="Detailed movement path")
    lens_focal_length: Optional[str] = Field(default=None, description="Estimated focal length")
    depth_of_field: Optional[str] = Field(default=None, description="Depth of field characteristics")
    motion_physics: Optional[str] = Field(default=None, description="Physics of movement in shot")
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
    time_of_day: Optional[str] = Field(default=None, description="Specific time of day")
    weather: Optional[str] = Field(default=None, description="Weather conditions")
    season: Optional[str] = Field(default=None, description="Season if determinable")
    description: str
    mood: Optional[str] = None
    # CRITICAL FIELDS - Blueprint demands these, but Optional for validation stability  
    lighting: Optional[str] = None
    physical_world: Optional[dict] = Field(default=None, description="Physical world details - architecture, signs, vehicles, objects - CRITICAL")
    human_subjects: Optional[list[dict]] = Field(default=None, description="Detailed human subject information - CRITICAL")
    
    # HIGHLY RECOMMENDED FIELDS
    lighting_type: Optional[str] = Field(default=None, description="Specific lighting type from standards")
    lighting_direction: Optional[str] = Field(default=None, description="Direction of light sources")
    lighting_temperature: Optional[str] = Field(default=None, description="Color temperature of lighting")
    color_palette: Optional[str] = None
    color_temperature: Optional[str] = Field(default=None, description="Overall color temperature")
    film_stock_resemblance: Optional[str] = Field(default=None, description="Which film stock this resembles")
    style: Optional[str] = None
    texture_details: Optional[dict] = Field(default=None, description="Surface and material textures")
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
    film_stock_look: Optional[str] = Field(default=None, description="Film stock characteristics")
    lens_characteristics: Optional[str] = Field(default=None, description="Lens and optical characteristics")
    overall_style: Optional[str] = None
    overall_mood: Optional[str] = None
    color_grading: Optional[str] = None
    cultural_context: Optional[str] = Field(default=None, description="Cultural and temporal context")
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
    
    # Kling 2.1 Pro first+last frame support
    use_first_last_frame: bool = Field(default=False, description="Whether this scene should use first+last frame approach")
    first_frame_prompt: Optional[str] = Field(default=None, description="Prompt for generating first frame image (T2I)")
    last_frame_prompt: Optional[str] = Field(default=None, description="Prompt for generating last frame image (T2I)")
    first_last_frame_reasoning: Optional[str] = Field(default=None, description="Explanation for why first+last frame is recommended")
    
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
