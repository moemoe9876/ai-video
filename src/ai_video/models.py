"""Domain models for AI video analysis and prompt generation."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

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

class LightingStyleBreakdown(BaseModel):
    """Structured lighting profile inferred for a shot or scene."""

    key_light: Optional[str] = Field(default=None, description="Primary key light description")
    fill_light: Optional[str] = Field(default=None, description="Fill light description")
    practical_lights: Optional[str] = Field(default=None, description="Visible practical lighting sources")
    mood: Optional[str] = Field(default=None, description="Lighting mood or ambience")


class CameraShotBreakdown(BaseModel):
    """Derived cinematography guidance for recreating a shot."""

    scene_id: str = Field(description="Scene-shot identifier (scene index + shot index)")
    camera_shot_type: Optional[str] = Field(default=None, description="Shot classification (e.g., Medium Shot)")
    camera_angle: Optional[str] = Field(default=None, description="Camera angle (high, low, dutch, etc.)")
    camera_height: Optional[str] = Field(default=None, description="Camera height guidance")
    camera_distance: Optional[str] = Field(default=None, description="Camera-to-subject distance guidance")
    framing_style: Optional[str] = Field(default=None, description="Framing or composition approach")
    lens_type_estimate: Optional[str] = Field(default=None, description="Lens choice or focal length estimate")
    depth_of_field: Optional[str] = Field(default=None, description="Depth of field guidance")
    lighting_style: LightingStyleBreakdown = Field(description="Structured lighting strategy for the shot")
    composition_notes: Optional[str] = Field(default=None, description="Key composition notes")
    set_design_notes: Optional[str] = Field(default=None, description="Relevant set or environment notes")
    camera_motion: Optional[str] = Field(default=None, description="Primary camera movement")
    cinematic_purpose: Optional[str] = Field(default=None, description="Purpose of the shot within the scene")
    recreation_guidance: Optional[str] = Field(default=None, description="Actionable guidance for recreating the shot")


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
    camera_breakdowns: list[CameraShotBreakdown] = Field(
        default_factory=list,
        description="Derived camera breakdowns for each shot in the scene"
    )
    
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
    camera_breakdowns: list[CameraShotBreakdown] = Field(
        default_factory=list,
        description="Camera analysis entries for each shot in the scene"
    )
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


class GlobalStyleProfile(BaseModel):
    """Shared creative direction applied to reimagined variants."""

    name: str = Field(description="Readable label for the global direction")
    description: Optional[str] = Field(default=None, description="Short description of the style")
    keywords: list[str] = Field(default_factory=list, description="Slug-friendly keywords that summarize the style")
    palette: Optional[str] = Field(default=None, description="Color palette shorthand")
    lighting: Optional[str] = Field(default=None, description="Signature lighting guidance")
    camera_direction: Optional[str] = Field(default=None, description="Camera movement/approach guidance")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Neon-soaked retrofuturism",
                "description": "Electric 1980s night city, analog grain with shimmering reflections",
                "keywords": ["neon-noir", "retro-future", "analog-grain"],
                "palette": "teal-magenta with sodium highlights",
                "lighting": "Moody sodium vapor wash with neon kickers",
                "camera_direction": "Handheld dolly pushes with roll-ins"
            }
        }


class ReimaginedVariant(BaseModel):
    """Single reimagined prompt variant for a scene."""

    variant_id: str = Field(description="Variant identifier within the scene")
    title: str = Field(description="Short handle for the variant")
    image_prompt: Optional[str] = Field(default=None, description="Text-to-image prompt")
    video_prompt: Optional[str] = Field(default=None, description="Text-to-video (or image-to-video) prompt")
    prompt: Optional[str] = Field(default=None, description="Legacy prompt field retained for backward compatibility")
    film_stock: Optional[str] = Field(default=None, description="Specific film stock treatment to emphasize")
    lens: Optional[str] = Field(default=None, description="Lens choice or optical treatment")
    mood: Optional[str] = Field(default=None, description="Emotional tone for this variant")
    cultural_context: Optional[str] = Field(default=None, description="Relevant cultural grounding cues")
    style_notes: Optional[str] = Field(default=None, description="Supplemental notes on style or mood")
    camera_focus: Optional[str] = Field(default=None, description="Camera direction or movement emphasis")
    lighting_focus: Optional[str] = Field(default=None, description="Lighting tone guidance")
    tags: list[str] = Field(default_factory=list, description="Keyword tags summarizing the variant")

    class Config:
        json_schema_extra = {
            "example": {
                "variant_id": "1",
                "title": "Midnight rain neon ride",
                "image_prompt": "Young couple racing through rain-soaked Shibuya on a vintage motorcycle, drenched neon signage, reflections shimmering on pavement, cinematic motion blur, 35mm anamorphic frame",
                "video_prompt": "Tracking shot swoops with the couple through Shibuya at night, neon halation reflecting off slick asphalt, handheld dolly push that eases into a slow orbit as rain streaks catch the sodium glow.",
                "film_stock": "Kodak Vision3 500T pushed for heavy grain and teal-magenta highlights",
                "lens": "50mm vintage prime with wide-open aperture and gentle vignette",
                "mood": "Electric, rain-soaked adrenaline",
                "cultural_context": "Late-90s Tokyo youth culture, Shibuya nightlife",
                "style_notes": "Blend Blade Runner color palette with Tokyo street photography grit",
                "camera_focus": "Low-slung tracking cam gliding inches above the asphalt",
                "lighting_focus": "Sodium vapor base with magenta neon spill",
                "tags": ["neon-noir", "rain", "tokyo", "anamorphic"]
            }
        }

    @field_validator("variant_id", mode="before")
    @classmethod
    def _coerce_variant_id(cls, value):
        if value is None:
            return value
        if isinstance(value, (int, float)):
            # Preserve zero-padding expectations by formatting as integer string
            return str(int(value))
        return str(value)

    @field_validator("image_prompt", "video_prompt", mode="after")
    @classmethod
    def _ensure_prompt_str(cls, value, info):
        if value is None:
            return value
        if isinstance(value, (int, float)):
            return str(value)
        return value

    @model_validator(mode="after")
    def _backfill_prompts(self) -> "ReimaginedVariant":
        # Maintain backward compatibility with legacy responses that only provided `prompt`
        if self.image_prompt is None and self.prompt is not None:
            self.image_prompt = self.prompt
        if self.video_prompt is None and self.prompt is not None:
            self.video_prompt = self.prompt
        return self


class ReimaginedScene(BaseModel):
    """Reimagined variants for a single source scene."""

    scene_index: int = Field(description="Index of the original scene")
    scene_title: Optional[str] = Field(default=None, description="Title or short label for the scene")
    location: Optional[str] = Field(default=None, description="Original location context")
    original_description: Optional[str] = Field(default=None, description="Summary from the source scene")
    original_prompt: Optional[str] = Field(default=None, description="Base prompt extracted from the detailed markdown")
    mood: Optional[str] = Field(default=None, description="Original mood annotation")
    reimagined_variants: list[ReimaginedVariant] = Field(default_factory=list, description="Variant prompts for this scene")
    notes: Optional[str] = Field(default=None, description="Optional cross-variant notes")

    class Config:
        json_schema_extra = {
            "example": {
                "scene_index": 3,
                "scene_title": "Roller rink embrace",
                "location": "Indoor roller rink with mirror ball",
                "original_description": "Couple holds hands while skating under warm lights",
                "mood": "Playful, nostalgic",
                "reimagined_variants": [],
                "notes": "Keep motion energy consistent across variants"
            }
        }


class ReimaginationResult(BaseModel):
    """Aggregate output of the ReimaginationAgent run."""

    video_id: str = Field(description="Video identifier associated with the prompts")
    source_file: str = Field(description="Path to the source markdown file")
    generated_at: datetime = Field(description="UTC timestamp when variants were generated")
    requested_style: Optional[str] = Field(default=None, description="User-provided style directive if any")
    user_prompt: Optional[str] = Field(default=None, description="Additional free-form user instructions")
    global_style: GlobalStyleProfile
    num_variants_per_scene: int = Field(description="Requested number of variants per scene")
    total_scenes: int = Field(description="Number of scenes processed")
    total_variants: int = Field(description="Total number of variants generated")
    scenes: list[ReimaginedScene] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict, description="Output artifact paths keyed by type")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "east_asian_90s_urban_romance_montage",
                "source_file": "assets/prompts/east_asian_90s_urban_romance_montage/prompts_detailed.md",
                "generated_at": "2024-10-02T06:30:00Z",
                "requested_style": "anime cyberpunk Tokyo",
                "user_prompt": "Emphasize VHS artifacting and dreamy slow-motion transitions",
                "global_style": {
                    "name": "Anime cyberpunk Tokyo",
                    "description": "Electric night city awash in holographic signage and rainy reflections",
                    "keywords": ["anime-cyberpunk", "holographic", "rain"],
                    "palette": "teal-magenta with golden highlights",
                    "lighting": "Moody volumetric neon",
                    "camera_direction": "Dynamic dolly sweeps with crane reveals"
                },
                "num_variants_per_scene": 3,
                "total_scenes": 5,
                "total_variants": 15,
                "scenes": [],
                "artifacts": {
                    "json": "assets/prompts/video_id/variant_prompts.json",
                    "markdown": "assets/prompts/video_id/variant_report.md"
                }
            }
        }
