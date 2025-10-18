"""
Prompt Generation from User Input Agent.

Converts a user's natural language prompt into a structured VideoReport
with scenes, shots, and entities, ready for prompt generation.
"""

import json
import re
from datetime import datetime
from typing import Optional

from ..gemini_client import GeminiVisionClient
from ..models import VideoReport, Scene, Shot, Entity, CameraShotBreakdown, LightingStyleBreakdown
from ..logging import get_logger, LogContext
from ..utils import generate_video_id
from ..paths import path_builder
from ..storage import save_model
from ..settings import settings
from .camera_analysis import CameraVisionAnalyzer

logger = get_logger(__name__)


class PromptGenerationFromUserInputAgent:
    """
    Agent for generating VideoReport from user's natural language prompt.
    
    This agent:
    1. Parses user prompt to extract duration, aesthetics, style, themes
    2. Strategizes optimal scene breakdown based on duration
    3. Generates synthetic scenes with shots and entities
    4. Produces a VideoReport compatible with existing pipeline
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = GeminiVisionClient(api_key=api_key, model=model)
        self.camera_analyzer = CameraVisionAnalyzer()
        self.config = settings.prompt_from_user if hasattr(settings, 'prompt_from_user') else self._get_defaults()
    
    def _get_defaults(self) -> dict:
        """Get default configuration for scene generation."""
        return {
            "default_scene_duration": 2.0,
            "min_scene_duration": 0.5,
            "max_scene_duration": 15.0,
            "max_scenes": 20,
            "default_fps": 24.0,
        }
    
    def generate_report_from_prompt(
        self,
        user_prompt: str,
        video_id: Optional[str] = None,
        save_report: bool = True
    ) -> VideoReport:
        """
        Generate a VideoReport from user's natural language prompt.
        
        Args:
            user_prompt: User's detailed prompt with aesthetics, style, duration, themes
            video_id: Optional custom video ID
            save_report: Whether to save the report to disk
        
        Returns:
            VideoReport with generated scenes and metadata
        """
        with LogContext(logger, f"Generating report from user prompt"):
            if video_id is None:
                video_id = generate_video_id(user_prompt)
            
            logger.info(f"Generated video ID: {video_id}")
            
            # Step 1: Parse user prompt to extract metadata
            parsed_data = self._parse_user_prompt(user_prompt)
            if "num_scenes" not in parsed_data:
                parsed_data["num_scenes"] = self._calculate_num_scenes(parsed_data.get("duration", 30.0))
            logger.info(f"Parsed prompt metadata: duration={parsed_data['duration']}s, scenes={parsed_data['num_scenes']}")
            
            # Step 2: Generate scene strategy
            scene_strategy = self._generate_scene_strategy(parsed_data, user_prompt)
            logger.info(f"Generated strategy for {len(scene_strategy)} scenes")
            
            # Step 3: Build VideoReport with synthetic scenes
            report = self._build_report(
                video_id=video_id,
                user_prompt=user_prompt,
                parsed_data=parsed_data,
                scene_strategy=scene_strategy
            )
            
            # Step 4: Save if requested
            if save_report:
                report_path = path_builder.get_report_path(video_id)
                save_model(report, report_path)
                logger.info(f"Report saved to: {report_path}")
            
            return report
    
    def _parse_user_prompt(self, user_prompt: str) -> dict:
        """
        Parse user prompt to extract key metadata.
        
        Uses Gemini to intelligently extract:
        - Duration (in seconds)
        - Overall style/aesthetic
        - Themes
        - Mood
        - Key subjects
        """
        extraction_prompt = f"""
        Analyze this user prompt and extract structured metadata:
        
        "{user_prompt}"
        
        Extract and return a JSON object with:
        - duration: (in seconds, extract from "30 seconds", "1 minute", etc. Default to 30 if not specified)
        - overall_style: (aesthetic/style description)
        - overall_mood: (emotional tone)
        - themes: (list of 3-5 key themes)
        - key_subjects: (main subjects/characters if any)
        - setting: (general setting/location)
        - cinematography_style: (visual style guidance)
        - color_palette: (dominant colors mentioned)
        - film_stock_look: (film stock or visual reference if mentioned)
        
        Return ONLY valid JSON, no other text.
        """
        
        try:
            response = self.client.chat(extraction_prompt, response_format="json")
            if isinstance(response, str):
                parsed = json.loads(response)
            else:
                parsed = response
            
            if isinstance(parsed, list):
                parsed = parsed[0] if parsed else {}
            
            # Ensure duration is a number
            duration_value = parsed.get("duration", 30)
            if isinstance(duration_value, str):
                # Try to extract number from string like "30 seconds" or "1 minute"
                match = re.search(r'(\d+)', duration_value)
                duration_value = int(match.group(1)) if match else 30
            elif not isinstance(duration_value, (int, float)):
                duration_value = 30
            
            parsed["duration"] = float(duration_value)
            parsed.setdefault("num_scenes", self._calculate_num_scenes(parsed["duration"]))

            defaults = {
                "overall_style": user_prompt,
                "overall_mood": "dynamic",
                "themes": ["unknown"],
                "key_subjects": [],
                "setting": "various",
                "cinematography_style": "cinematic",
                "color_palette": "varied",
                "film_stock_look": "digital",
            }
            for key, default in defaults.items():
                if parsed.get(key) is None:
                    parsed[key] = default
            
            if not isinstance(parsed.get("themes"), list):
                parsed["themes"] = [str(parsed["themes"])]
            if not isinstance(parsed.get("key_subjects"), list):
                parsed["key_subjects"] = [str(parsed["key_subjects"])]

            return parsed
        except Exception as e:
            logger.warning(f"Failed to parse prompt with Gemini: {e}. Using defaults.")
            default_duration = 30.0
            return {
                "duration": default_duration,
                "overall_style": user_prompt,
                "overall_mood": "dynamic",
                "themes": ["unknown"],
                "key_subjects": [],
                "setting": "various",
                "cinematography_style": "cinematic",
                "color_palette": "varied",
                "film_stock_look": "digital",
                "num_scenes": self._calculate_num_scenes(default_duration)
            }
    
    def _generate_scene_strategy(self, parsed_data: dict, user_prompt: str) -> list:
        """
        Generate optimal scene breakdown strategy using Gemini.
        
        Returns list of scene strategies with:
        - scene_index
        - duration
        - location
        - description
        - mood
        - key_action
        """
        duration = parsed_data["duration"]
        num_scenes = parsed_data.get("num_scenes")
        if isinstance(num_scenes, str):
            num_scenes = int(re.search(r'\d+', num_scenes).group()) if re.search(r'\d+', num_scenes) else None
        if not isinstance(num_scenes, int) or num_scenes <= 0:
            num_scenes = self._calculate_num_scenes(duration)
            parsed_data["num_scenes"] = num_scenes
        
        strategy_prompt = f"""
        Create a detailed scene breakdown strategy for a {duration}-second video.
        Total scenes: {num_scenes} (distribute duration evenly across scenes)
        
        User's vision:
        "{user_prompt}"
        
        Overall style: {parsed_data.get('overall_style', 'cinematic')}
        Overall mood: {parsed_data.get('overall_mood', 'dynamic')}
        Themes: {', '.join(parsed_data.get('themes', []))}
        Setting: {parsed_data.get('setting', 'various')}
        
        For each scene, create a JSON object with:
        - scene_number: (1 to {num_scenes})
        - duration: (in seconds, sum must equal {duration})
        - location: (where this scene takes place)
        - description: (2-3 sentence scene description)
        - mood: (emotional tone for this scene)
        - key_action: (main action or event in this scene)
        - visual_elements: (key visual elements to emphasize)
        - camera_style: (recommended camera approach)
        
        Return a JSON array of {num_scenes} scene objects.
        Return ONLY valid JSON array, no other text.
        """
        
        try:
            response = self.client.chat(strategy_prompt, response_format="json")
            if isinstance(response, str):
                scenes = json.loads(response)
            else:
                scenes = response
            
            # Validate and normalize
            if isinstance(scenes, dict):
                scenes = [scenes]
            elif not isinstance(scenes, list):
                scenes = []
            
            # Ensure we have the right number of scenes
            scenes = scenes[:num_scenes]
            while len(scenes) < num_scenes:
                # Fill missing scenes with defaults
                scenes.append({
                    "scene_number": len(scenes) + 1,
                    "duration": duration / num_scenes,
                    "location": "Scene location",
                    "description": "Scene description",
                    "mood": "dynamic",
                    "key_action": "Action",
                    "visual_elements": [],
                    "camera_style": "cinematic"
                })
            
            return scenes
        except Exception as e:
            logger.warning(f"Failed to generate scene strategy: {e}. Using simple breakdown.")
            # Fallback: simple even split
            scene_duration = duration / num_scenes
            scenes = []
            for i in range(num_scenes):
                scenes.append({
                    "scene_number": i + 1,
                    "duration": scene_duration,
                    "location": f"Scene {i + 1} location",
                    "description": f"Scene {i + 1}: part of the overall narrative",
                    "mood": parsed_data.get("overall_mood", "dynamic"),
                    "key_action": "Scene action",
                    "visual_elements": [],
                    "camera_style": "cinematic"
                })
            return scenes
    
    def _calculate_num_scenes(self, duration: float) -> int:
        """
        Calculate optimal number of scenes based on duration.
        
        Strategy: aim for scenes of 5-8 seconds each for pacing.
        """
        default_scene_duration = self.config.get("default_scene_duration", 6.0)
        max_scenes = self.config.get("max_scenes", 20)
        
        num_scenes = max(1, min(int(duration / default_scene_duration), max_scenes))
        return num_scenes
    
    def _build_report(
        self,
        video_id: str,
        user_prompt: str,
        parsed_data: dict,
        scene_strategy: list
    ) -> VideoReport:
        """Build a VideoReport from parsed data and scene strategy."""
        total_duration = sum(s.get("duration", 6.0) for s in scene_strategy)
        
        scenes = []
        current_time = 0.0
        
        for scene_data in scene_strategy:
            scene_duration = scene_data.get("duration", 6.0)
            scene_index = scene_data.get("scene_number", len(scenes) + 1)
            
            scene = self._build_scene(
                scene_index=scene_index,
                start_time=current_time,
                duration=scene_duration,
                scene_data=scene_data,
                parsed_data=parsed_data
            )
            scenes.append(scene)
            current_time += scene_duration
        
        report = VideoReport(
            video_id=video_id,
            source=f"user_prompt:{video_id}",
            duration=total_duration,
            fps=self.config.get("default_fps", 24.0),
            resolution="1920x1080",
            title=parsed_data.get("overall_style", "Generated Video"),
            summary=user_prompt,
            overall_style=parsed_data.get("overall_style", "cinematic"),
            overall_mood=parsed_data.get("overall_mood", "dynamic"),
            color_grading=parsed_data.get("color_palette", "varied"),
            film_stock_look=parsed_data.get("film_stock_look", "digital"),
            cultural_context=parsed_data.get("setting", "various"),
            scenes=scenes,
            main_entities=[],
            created_at=datetime.now()
        )
        
        return report
    
    def _build_scene(
        self,
        scene_index: int,
        start_time: float,
        duration: float,
        scene_data: dict,
        parsed_data: dict
    ) -> Scene:
        """Build a Scene object from scene strategy data."""
        end_time = start_time + duration
        
        # Generate 2-4 shots for this scene
        num_shots = max(2, min(4, int(duration / 2)))
        shots = self._generate_shots(
            scene_index=scene_index,
            num_shots=num_shots,
            start_time=start_time,
            total_duration=duration,
            scene_data=scene_data
        )
        
        # Create camera breakdowns for each shot
        camera_breakdowns = [
            self._create_camera_breakdown(
                scene_index=scene_index,
                shot_index=shot.shot_index,
                shot=shot,
                scene_data=scene_data
            )
            for shot in shots
        ]
        
        # Create key entities
        key_entities = self._extract_entities_from_scene(scene_data, parsed_data)
        
        scene = Scene(
            scene_index=scene_index,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            location=scene_data.get("location", "Scene location"),
            description=scene_data.get("description", "Scene description"),
            mood=scene_data.get("mood", "dynamic"),
            lighting=self._generate_lighting_description(scene_data),
            time_of_day=self._infer_time_of_day(scene_data),
            weather=None,
            season=None,
            color_palette=parsed_data.get("color_palette", "varied"),
            color_temperature=self._infer_color_temperature(parsed_data),
            film_stock_resemblance=parsed_data.get("film_stock_look", "digital"),
            style=parsed_data.get("cinematography_style", "cinematic"),
            shots=shots,
            key_entities=key_entities,
            camera_breakdowns=camera_breakdowns
        )
        
        return scene
    
    def _generate_shots(
        self,
        scene_index: int,
        num_shots: int,
        start_time: float,
        total_duration: float,
        scene_data: dict
    ) -> list:
        """Generate shot objects for a scene."""
        shots = []
        shot_duration = total_duration / num_shots
        
        for shot_idx in range(num_shots):
            shot_start = start_time + (shot_idx * shot_duration)
            shot_end = shot_start + shot_duration
            
            shot = Shot(
                shot_index=shot_idx + 1,
                start_time=shot_start,
                end_time=shot_end,
                duration=shot_duration,
                description=scene_data.get("description", "Shot description"),
                action=scene_data.get("key_action", "Action"),
                shot_type=self._infer_shot_type(shot_idx, num_shots),
                camera_movement=self._infer_camera_movement(shot_idx, num_shots),
                camera_description=f"Shot {shot_idx + 1}: {scene_data.get('camera_style', 'cinematic')} approach",
                camera_position="Center frame",
                camera_angle_degrees="0 (eye level)",
                camera_distance_meters="3-5",
                camera_height_meters="1.5",
                subject_position_frame="Rule of thirds",
                spatial_relationships="Subject centered with environmental context",
                camera_movement_trajectory=None,
                lens_focal_length="50mm (standard)",
                depth_of_field="Shallow to medium",
                motion_physics="Smooth camera work",
                entities=[]
            )
            shots.append(shot)
        
        return shots
    
    def _infer_shot_type(self, shot_idx: int, total_shots: int) -> str:
        """Infer shot type based on position in sequence."""
        if shot_idx == 0:
            return "wide"  # Establishing shot
        elif shot_idx == total_shots - 1:
            return "close_up"  # Closing detail
        else:
            return "medium"
    
    def _infer_camera_movement(self, shot_idx: int, total_shots: int) -> str:
        """Infer camera movement variation."""
        movements = ["static", "tracking", "zoom_in", "pan_left", "dolly"]
        return movements[shot_idx % len(movements)]
    
    def _generate_lighting_description(self, scene_data: dict) -> str:
        """Generate lighting description from scene data."""
        visual_elements = scene_data.get("visual_elements", [])
        if visual_elements and isinstance(visual_elements, list):
            return f"Dynamic lighting with {', '.join(visual_elements[:2])} emphasis"
        return "Cinematic three-point lighting"
    
    def _infer_time_of_day(self, scene_data: dict) -> Optional[str]:
        """Infer time of day from scene description."""
        description = (scene_data.get("description", "") + " " + scene_data.get("location", "")).lower()
        
        if any(word in description for word in ["night", "dark", "evening", "dusk"]):
            return "night"
        elif any(word in description for word in ["morning", "sunrise", "dawn"]):
            return "morning"
        elif any(word in description for word in ["sunset", "golden"]):
            return "sunset"
        else:
            return "daytime"
    
    def _infer_color_temperature(self, parsed_data: dict) -> Optional[str]:
        """Infer color temperature from overall style."""
        style_raw = parsed_data.get("overall_style", "")
        palette_raw = parsed_data.get("color_palette", "")

        style = style_raw.lower() if isinstance(style_raw, str) else ""
        if isinstance(style_raw, list):
            style = " ".join(str(item) for item in style_raw).lower()

        palette = palette_raw.lower() if isinstance(palette_raw, str) else ""
        if isinstance(palette_raw, list):
            palette = " ".join(str(item) for item in palette_raw).lower()
        
        combined = style + " " + palette
        
        if any(word in combined for word in ["warm", "golden", "orange", "amber"]):
            return "warm (3200K)"
        elif any(word in combined for word in ["cool", "blue", "cyan", "cold"]):
            return "cool (5600K)"
        else:
            return "neutral (4000K)"
    
    def _create_camera_breakdown(
        self,
        scene_index: int,
        shot_index: int,
        shot: Shot,
        scene_data: dict
    ) -> CameraShotBreakdown:
        """Create a camera breakdown for a shot using CameraVisionAnalyzer."""
        # Use the camera analyzer to infer professional-grade camera parameters
        shot_type = self.camera_analyzer._format_shot_type(shot.shot_type)
        camera_angle = self.camera_analyzer._infer_camera_angle(shot)
        camera_height = self.camera_analyzer._infer_camera_height(shot)
        camera_distance = self.camera_analyzer._infer_camera_distance(shot)
        framing_style = self.camera_analyzer._infer_framing_style(shot)
        lens_type = self.camera_analyzer._infer_lens_type(shot)
        depth_of_field = self.camera_analyzer._infer_depth_of_field(shot)
        camera_motion = self.camera_analyzer._infer_camera_motion(shot)
        
        lighting_style = LightingStyleBreakdown(
            key_light=scene_data.get("camera_style", "Cinematic key light"),
            fill_light="Balanced fill for depth",
            practical_lights=None,
            mood=scene_data.get("mood", "dynamic")
        )
        
        composition_notes = self.camera_analyzer._build_composition_notes(
            Scene(
                scene_index=scene_index,
                start_time=shot.start_time,
                end_time=shot.end_time,
                duration=shot.duration,
                location=scene_data.get("location", "Scene location"),
                description=scene_data.get("description", "Scene description"),
                shots=[shot],
                key_entities=[]
            ),
            shot
        )
        
        recreation_guidance = self.camera_analyzer._build_recreation_guidance(
            camera_height,
            camera_distance,
            lens_type,
            lighting_style,
            framing_style,
            camera_motion,
        )
        
        return CameraShotBreakdown(
            scene_id=f"scene_{scene_index}_shot_{shot_index}",
            camera_shot_type=shot_type,
            camera_angle=camera_angle,
            camera_height=camera_height,
            camera_distance=camera_distance,
            framing_style=framing_style,
            lens_type_estimate=lens_type,
            depth_of_field=depth_of_field,
            lighting_style=lighting_style,
            composition_notes=composition_notes,
            set_design_notes=f"Location: {scene_data.get('location', 'Scene location')}",
            camera_motion=camera_motion,
            cinematic_purpose=scene_data.get("key_action", "Narrative action"),
            recreation_guidance=recreation_guidance
        )
    
    def _extract_entities_from_scene(self, scene_data: dict, parsed_data: dict) -> list:
        """Extract or create entities from scene and parsed data."""
        entities = []
        
        # Create entity from key_subjects if available
        key_subjects = parsed_data.get("key_subjects", [])
        if isinstance(key_subjects, str):
            key_subjects = [key_subjects]
        
        for subject in key_subjects:
            if subject:
                entity = Entity(
                    name=subject,
                    type="person" if any(word in subject.lower() for word in ["person", "character", "man", "woman", "man", "people"]) else "object",
                    description=f"Key subject: {subject}",
                    appearance=None
                )
                entities.append(entity)
        
        return entities
