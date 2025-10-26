"""Video Analysis Agent - Analyzes videos and produces structured reports."""

from pathlib import Path
from typing import Union, Optional, List
from datetime import datetime

from ..models import VideoReport, Scene, Shot, Entity
from ..gemini_client import GeminiVisionClient
from ..paths import path_builder
from ..storage import save_model, write_json
from ..utils import generate_video_id
from ..logging import get_logger, LogContext
from .camera_analysis import CameraVisionAnalyzer

logger = get_logger(__name__)

class VideoAnalysisAgent:
    """Agent for analyzing videos and generating structured reports."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = GeminiVisionClient(api_key=api_key, model=model)
        self.camera_analyzer = CameraVisionAnalyzer()
    
    def analyze(
        self,
        video_source: Union[str, Path],
        video_id: Optional[str] = None,
        save_report: bool = True,
        start_offset: Optional[str] = None,
        end_offset: Optional[str] = None,
        fps: Optional[int] = None
    ) -> VideoReport:
        """
        Analyze a video and produce a VideoReport.
        
        Args:
            video_source: Path to video file or YouTube URL
            video_id: Optional custom video ID
            save_report: Whether to save the report to disk
            start_offset: Optional start time offset
            end_offset: Optional end time offset
            fps: Optional frames per second for sampling
        
        Returns:
            VideoReport with full analysis
        """
        with LogContext(logger, f"Video analysis: {video_source}"):
            if video_id is None:
                video_id = generate_video_id(str(video_source))
            
            logger.info(f"Generated video ID: {video_id}")
            
            response = self.client.analyze_video(
                video_source=video_source,
                use_blueprint=True,
                start_offset=start_offset,
                end_offset=end_offset,
                fps=fps,
                response_format="json"
            )
            
            if "error" in response:
                logger.error(f"Analysis failed: {response['error']}")
                raise RuntimeError(f"Video analysis failed: {response['error']}")
            
            report = self._build_report(response, video_id, str(video_source))
            self._attach_camera_breakdowns(report)
            if save_report:
                self._save_camera_breakdowns(report)
            
            if save_report:
                # Use the video_id from the report (which may be Gemini-generated) for the filename
                report_video_id = report.video_id if hasattr(report, 'video_id') and report.video_id else video_id
                report_path = path_builder.get_report_path(report_video_id)
                save_model(report, report_path)
                logger.info(f"Report saved to: {report_path}")
            
            return report
    
    def _build_report(self, analysis_data: dict, video_id: str, source: str) -> VideoReport:
        """Build a VideoReport from raw analysis data."""
        report_data = {
            "video_id": analysis_data.get("video_id", video_id),
            "source": source,
            "duration": analysis_data.get("duration", 0.0),
            "fps": analysis_data.get("fps"),
            "resolution": analysis_data.get("resolution"),
            "title": analysis_data.get("title"),
            "summary": analysis_data.get("summary", ""),
            "film_stock_look": analysis_data.get("film_stock_look"),
            "lens_characteristics": analysis_data.get("lens_characteristics"),
            "overall_style": analysis_data.get("overall_style"),
            "overall_mood": analysis_data.get("overall_mood"),
            "color_grading": analysis_data.get("color_grading"),
            "cultural_context": analysis_data.get("cultural_context"),
            "created_at": datetime.now(),
        }
        
        scenes = []
        for scene_data in analysis_data.get("scenes", []):
            scene = self._build_scene(scene_data)
            scenes.append(scene)
        
        report_data["scenes"] = self._normalize_scene_timings(scenes, report_data["duration"])
        
        main_entities = []
        for entity_data in analysis_data.get("main_entities", []):
            if isinstance(entity_data, dict):
                # Handle entity_id vs name inconsistency
                if "entity_id" in entity_data and "name" not in entity_data:
                    entity_data["name"] = entity_data.pop("entity_id")
                entity = Entity(**entity_data)
                main_entities.append(entity)
            elif isinstance(entity_data, str):
                entity = Entity(name=entity_data, type="unknown")
                main_entities.append(entity)
        
        report_data["main_entities"] = main_entities
        
        return VideoReport(**report_data)
    
    def _build_scene(self, scene_data: dict) -> Scene:
        """Build a Scene from raw data."""
        shots = []
        for shot_data in scene_data.get("shots", []):
            if isinstance(shot_data, dict):
                shot = self._build_shot(shot_data)
                shots.append(shot)
        
        entities = []
        for entity_data in scene_data.get("key_entities", []):
            if isinstance(entity_data, dict):
                # Handle entity_id vs name inconsistency
                if "entity_id" in entity_data and "name" not in entity_data:
                    entity_data["name"] = entity_data.pop("entity_id")
                entity = Entity(**entity_data)
                entities.append(entity)
            elif isinstance(entity_data, str):
                entity = Entity(name=entity_data, type="unknown")
                entities.append(entity)
        
        # Handle lighting - might be string or dict
        lighting_data = scene_data.get("lighting")
        if isinstance(lighting_data, dict):
            # Convert dict to string description
            lighting_str = lighting_data.get("type", "")
            if "direction" in lighting_data:
                lighting_str += f", {lighting_data['direction']}"
            if "quality" in lighting_data:
                lighting_str += f", {lighting_data['quality']}"
            if "temperature" in lighting_data:
                lighting_str += f", {lighting_data['temperature']}"
            lighting = lighting_str if lighting_str else None
        else:
            lighting = lighting_data
        
        scene_dict = {
            "scene_index": scene_data.get("scene_index", 0),
            "start_time": scene_data.get("start_time", 0.0),
            "end_time": scene_data.get("end_time", 0.0),
            "duration": scene_data.get("duration", 0.0),
            "location": scene_data.get("location", "Unknown"),
            "time_of_day": scene_data.get("time_of_day"),
            "weather": scene_data.get("weather"),
            "season": scene_data.get("season"),
            "description": scene_data.get("description", ""),
            "mood": scene_data.get("mood"),
            "lighting": lighting,  # REQUIRED
            "lighting_type": scene_data.get("lighting_type"),
            "lighting_direction": scene_data.get("lighting_direction"),
            "lighting_temperature": scene_data.get("lighting_temperature"),
            "color_palette": scene_data.get("color_palette"),
            "color_temperature": scene_data.get("color_temperature"),
            "film_stock_resemblance": scene_data.get("film_stock_resemblance"),
            "style": scene_data.get("style"),
            "physical_world": scene_data.get("physical_world"),  # REQUIRED
            "human_subjects": scene_data.get("human_subjects") or [],  # REQUIRED - empty list if no people visible
            "texture_details": scene_data.get("texture_details"),
            "shots": shots,
            "key_entities": entities,
        }
        
        return Scene(**scene_dict)
    
    def _build_shot(self, shot_data: dict) -> Shot:
        """Build a Shot from raw data."""
        entities = []
        for entity_data in shot_data.get("entities", []):
            if isinstance(entity_data, dict):
                # Handle entity_id vs name inconsistency
                if "entity_id" in entity_data and "name" not in entity_data:
                    entity_data["name"] = entity_data.pop("entity_id")
                entity = Entity(**entity_data)
                entities.append(entity)
            elif isinstance(entity_data, str):
                entity = Entity(name=entity_data, type="unknown")
                entities.append(entity)
        
        # Helper to convert dict to string
        def dict_to_str(data):
            if isinstance(data, dict):
                return ". ".join(f"{v}" for k, v in data.items() if v)
            return data
        
        shot_dict = {
            "shot_index": shot_data.get("shot_index", 0),
            "start_time": shot_data.get("start_time", 0.0),
            "end_time": shot_data.get("end_time", 0.0),
            "duration": shot_data.get("duration", 0.0),
            "description": shot_data.get("description", ""),
            "action": shot_data.get("action", ""),
            "shot_type": shot_data.get("shot_type"),
            "camera_movement": shot_data.get("camera_movement"),
            "camera_description": shot_data.get("camera_description"),
            # REQUIRED fields - NO DEFAULTS, Gemini MUST provide these
            "camera_position": dict_to_str(shot_data.get("camera_position")),
            "camera_angle_degrees": dict_to_str(shot_data.get("camera_angle_degrees")),
            "camera_distance_meters": dict_to_str(shot_data.get("camera_distance_meters")),
            "camera_height_meters": dict_to_str(shot_data.get("camera_height_meters")),
            "subject_position_frame": dict_to_str(shot_data.get("subject_position_frame")),
            "spatial_relationships": dict_to_str(shot_data.get("spatial_relationships")),
            # OPTIONAL fields
            "camera_movement_trajectory": dict_to_str(shot_data.get("camera_movement_trajectory")),
            "lens_focal_length": dict_to_str(shot_data.get("lens_focal_length")),
            "depth_of_field": dict_to_str(shot_data.get("depth_of_field")),
            "motion_physics": dict_to_str(shot_data.get("motion_physics")),
            "entities": entities,
        }
        
        return Shot(**shot_dict)

    @staticmethod
    def _normalize_scene_timings(scenes: List[Scene], video_duration: float) -> List[Scene]:
        """Normalize scene and shot timings to cover the full video duration."""
        if not scenes:
            return scenes

        min_scene_duration = 0.1  # seconds
        min_shot_duration = 0.05  # seconds
        rounding_decimals = 3

        sorted_scenes = sorted(scenes, key=lambda s: (s.start_time, s.scene_index))

        # Use scene durations as weights; ensure no zero weights
        scene_weights = []
        for scene in sorted_scenes:
            raw_duration = scene.duration or (scene.end_time - scene.start_time)
            if raw_duration is None or raw_duration <= 0:
                raw_duration = min_scene_duration
            scene_weights.append(max(raw_duration, min_scene_duration))

        total_weight = sum(scene_weights)
        if video_duration and video_duration > 0 and total_weight > 0:
            scene_scale = video_duration / total_weight
        else:
            scene_scale = 1.0

        normalized_scenes: List[Scene] = []
        current_time = 0.0

        for idx, (scene, weight) in enumerate(zip(sorted_scenes, scene_weights), start=1):
            duration = max(weight * scene_scale, min_scene_duration)
            start_time = current_time
            end_time = start_time + duration
            current_time = end_time

            # Normalize shots within the scene
            shots = sorted(scene.shots, key=lambda sh: (sh.start_time, sh.shot_index))
            shot_weights = []
            for shot in shots:
                raw_shot_duration = shot.duration or (shot.end_time - shot.start_time)
                if raw_shot_duration is None or raw_shot_duration <= 0:
                    raw_shot_duration = min_shot_duration
                shot_weights.append(max(raw_shot_duration, min_shot_duration))

            total_shot_weight = sum(shot_weights)
            shot_scale = (duration / total_shot_weight) if total_shot_weight > 0 else 0.0

            normalized_shots = []
            shot_current = start_time
            for shot_idx, (shot, shot_weight) in enumerate(zip(shots, shot_weights), start=1):
                shot_duration = max(shot_weight * shot_scale, min_shot_duration) if shot_scale else duration / max(len(shots), 1)
                shot_start = shot_current
                shot_end = shot_start + shot_duration
                shot_current = shot_end

                normalized_shots.append(
                    shot.model_copy(
                        update={
                            "shot_index": shot_idx,
                            "start_time": round(shot_start, rounding_decimals),
                            "end_time": round(shot_end, rounding_decimals),
                            "duration": round(max(shot_end - shot_start, min_shot_duration), rounding_decimals),
                        }
                    )
                )

            # Ensure last shot lines up with scene end
            if normalized_shots:
                last_shot = normalized_shots[-1]
                normalized_shots[-1] = last_shot.model_copy(
                    update={
                        "end_time": round(end_time, rounding_decimals),
                        "duration": round(max(end_time - last_shot.start_time, min_shot_duration), rounding_decimals),
                    }
                )

            normalized_scene = scene.model_copy(
                update={
                    "scene_index": idx,
                    "start_time": round(start_time, rounding_decimals),
                    "end_time": round(end_time, rounding_decimals),
                    "duration": round(max(end_time - start_time, min_scene_duration), rounding_decimals),
                    "shots": normalized_shots,
                }
            )
            normalized_scenes.append(normalized_scene)

        # Adjust final scene to exactly match video duration
        if video_duration and normalized_scenes:
            final_scene = normalized_scenes[-1]
            final_end_time = round(video_duration, rounding_decimals)
            if final_scene.end_time != final_end_time:
                final_scene = final_scene.model_copy(
                    update={
                        "end_time": final_end_time,
                        "duration": round(max(final_end_time - final_scene.start_time, min_scene_duration), rounding_decimals),
                    }
                )
                if final_scene.shots:
                    final_shot = final_scene.shots[-1]
                    final_scene.shots[-1] = final_shot.model_copy(
                        update={
                            "end_time": final_end_time,
                            "duration": round(max(final_end_time - final_shot.start_time, min_shot_duration), rounding_decimals),
                        }
                    )
                normalized_scenes[-1] = final_scene

        return normalized_scenes

    def _attach_camera_breakdowns(self, report: VideoReport) -> None:
        """Enrich each scene with structured camera analysis."""

        for scene in report.scenes:
            scene.camera_breakdowns = self.camera_analyzer.analyze_scene(scene, report)

    def _save_camera_breakdowns(self, report: VideoReport) -> None:
        """Persist camera analysis to a standalone JSON artifact."""

        analysis_path = path_builder.get_camera_analysis_path(report.video_id)
        scenes_payload = []
        for scene in report.scenes:
            breakdowns = [b.model_dump(mode="json") for b in scene.camera_breakdowns]
            scenes_payload.append(
                {
                    "scene_index": scene.scene_index,
                    "start_time": scene.start_time,
                    "end_time": scene.end_time,
                    "camera_breakdowns": breakdowns,
                }
            )

        payload = {
            "video_id": report.video_id,
            "source": report.source,
            "created_at": report.created_at.isoformat() if hasattr(report.created_at, "isoformat") else None,
            "scenes": scenes_payload,
        }

        write_json(payload, analysis_path)
        logger.info(f"Camera analysis saved to: {analysis_path}")
