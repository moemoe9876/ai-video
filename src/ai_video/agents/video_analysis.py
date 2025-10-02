"""Video Analysis Agent - Analyzes videos and produces structured reports."""

from pathlib import Path
from typing import Union, Optional
from datetime import datetime

from ..models import VideoReport, Scene, Shot, Entity
from ..gemini_client import GeminiVisionClient
from ..paths import path_builder
from ..storage import save_model
from ..utils import generate_video_id
from ..logging import get_logger, LogContext

logger = get_logger(__name__)

class VideoAnalysisAgent:
    """Agent for analyzing videos and generating structured reports."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = GeminiVisionClient(api_key=api_key, model=model)
    
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
            
            if save_report:
                report_path = path_builder.get_report_path(video_id)
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
            "overall_style": analysis_data.get("overall_style"),
            "overall_mood": analysis_data.get("overall_mood"),
            "color_grading": analysis_data.get("color_grading"),
            "created_at": datetime.now(),
        }
        
        scenes = []
        for scene_data in analysis_data.get("scenes", []):
            scene = self._build_scene(scene_data)
            scenes.append(scene)
        
        report_data["scenes"] = scenes
        
        main_entities = []
        for entity_data in analysis_data.get("main_entities", []):
            entity = Entity(**entity_data)
            main_entities.append(entity)
        
        report_data["main_entities"] = main_entities
        
        return VideoReport(**report_data)
    
    def _build_scene(self, scene_data: dict) -> Scene:
        """Build a Scene from raw data."""
        shots = []
        for shot_data in scene_data.get("shots", []):
            shot = self._build_shot(shot_data)
            shots.append(shot)
        
        entities = []
        for entity_data in scene_data.get("key_entities", []):
            entity = Entity(**entity_data)
            entities.append(entity)
        
        scene_dict = {
            "scene_index": scene_data.get("scene_index", 0),
            "start_time": scene_data.get("start_time", 0.0),
            "end_time": scene_data.get("end_time", 0.0),
            "duration": scene_data.get("duration", 0.0),
            "location": scene_data.get("location", "Unknown"),
            "description": scene_data.get("description", ""),
            "mood": scene_data.get("mood"),
            "lighting": scene_data.get("lighting"),
            "color_palette": scene_data.get("color_palette"),
            "style": scene_data.get("style"),
            "shots": shots,
            "key_entities": entities,
        }
        
        return Scene(**scene_dict)
    
    def _build_shot(self, shot_data: dict) -> Shot:
        """Build a Shot from raw data."""
        entities = []
        for entity_data in shot_data.get("entities", []):
            entity = Entity(**entity_data)
            entities.append(entity)
        
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
            "entities": entities,
        }
        
        return Shot(**shot_dict)
