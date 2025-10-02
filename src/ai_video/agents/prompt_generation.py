"""Prompt Generation Agent - Converts video analysis into generation prompts."""

from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ..models import (
    VideoReport, Scene, Shot, Entity,
    PromptSpec, PromptBundle, PromptType
)
from ..paths import path_builder
from ..storage import save_model, load_model
from ..settings import settings
from ..logging import get_logger, LogContext
from ..utils import format_timestamp

logger = get_logger(__name__)

class PromptGenerationAgent:
    """Agent for generating prompts from video analysis."""
    
    def __init__(self):
        self.config = settings.prompts
    
    def generate_prompts(
        self,
        report: VideoReport,
        save_bundles: bool = True
    ) -> List[PromptBundle]:
        """
        Generate prompt bundles for all scenes in the report.
        
        Args:
            report: VideoReport to generate prompts from
            save_bundles: Whether to save prompt bundles to disk
        
        Returns:
            List of PromptBundle objects
        """
        with LogContext(logger, f"Generating prompts for video: {report.video_id}"):
            bundles = []
            
            for scene in report.scenes:
                bundle = self._generate_scene_bundle(scene, report)
                bundles.append(bundle)
                
                if save_bundles:
                    bundle_path = path_builder.get_scene_prompt_path(
                        report.video_id, scene.scene_index
                    )
                    save_model(bundle, bundle_path)
                    logger.info(f"Saved prompt bundle: {bundle_path}")
            
            logger.info(f"Generated {len(bundles)} prompt bundles")
            return bundles
    
    def _generate_scene_bundle(self, scene: Scene, report: VideoReport) -> PromptBundle:
        """Generate a prompt bundle for a single scene."""
        image_prompts = []
        video_prompts = []
        shot_descriptions = []
        
        for shot in scene.shots:
            img_prompt = self._generate_image_prompt(shot, scene, report)
            image_prompts.append(img_prompt)
            
            vid_prompt = self._generate_video_prompt(shot, scene, report)
            video_prompts.append(vid_prompt)
            
            shot_desc = self._create_shot_description(shot, scene)
            shot_descriptions.append(shot_desc)
        
        if not scene.shots:
            img_prompt = self._generate_scene_image_prompt(scene, report)
            image_prompts.append(img_prompt)
            
            vid_prompt = self._generate_scene_video_prompt(scene, report)
            video_prompts.append(vid_prompt)
        
        notes = self._generate_notes(scene, report)
        
        bundle = PromptBundle(
            scene_index=scene.scene_index,
            start_time=scene.start_time,
            end_time=scene.end_time,
            duration=scene.duration,
            image_prompts=image_prompts,
            video_prompts=video_prompts,
            shot_descriptions=shot_descriptions,
            notes=notes,
            created_at=datetime.now()
        )
        
        return bundle
    
    def _generate_image_prompt(self, shot: Shot, scene: Scene, report: VideoReport) -> PromptSpec:
        """Generate a text-to-image prompt for a shot."""
        subject = self._extract_subject(shot, scene)
        action = shot.action
        scene_desc = self._build_scene_description(scene)
        camera = self._build_camera_description(shot)
        lighting = scene.lighting or report.color_grading or "natural lighting"
        style = scene.style or report.overall_style or "cinematic, realistic"
        
        prompt_parts = [subject]
        
        if action:
            prompt_parts.append(action)
        
        prompt_parts.append(f"in {scene_desc}")
        
        if self.config.include_camera_details and camera:
            prompt_parts.append(camera)
        
        if self.config.include_lighting and lighting:
            prompt_parts.append(lighting)
        
        if self.config.include_style and style:
            prompt_parts.append(style)
        
        prompt_text = ". ".join(prompt_parts) + "."
        
        if self.config.max_prompt_length and len(prompt_text) > self.config.max_prompt_length:
            prompt_text = prompt_text[:self.config.max_prompt_length - 3] + "..."
        
        return PromptSpec(
            prompt_type=PromptType.TEXT_TO_IMAGE,
            text=prompt_text,
            subject=subject,
            action=action,
            scene=scene_desc,
            camera=camera if self.config.include_camera_details else None,
            lighting=lighting if self.config.include_lighting else None,
            style=style if self.config.include_style else None,
            negative_prompt="blur, blurry, out of focus, distorted, low quality, pixelated, watermark"
        )
    
    def _generate_video_prompt(self, shot: Shot, scene: Scene, report: VideoReport) -> PromptSpec:
        """Generate a text-to-video or image-to-video prompt for a shot."""
        subject = self._extract_subject(shot, scene)
        action = shot.action
        scene_desc = self._build_scene_description(scene)
        camera = self._build_camera_movement_description(shot)
        lighting = scene.lighting or report.color_grading or "natural lighting"
        style = scene.style or report.overall_style or "cinematic"
        
        prompt_parts = [subject, action, f"in {scene_desc}"]
        
        if self.config.include_camera_details and camera:
            prompt_parts.append(camera)
        
        if self.config.include_lighting and lighting:
            prompt_parts.append(f"with {lighting}")
        
        if self.config.include_style and style:
            prompt_parts.append(f"{style} style")
        
        prompt_text = ". ".join(prompt_parts) + "."
        
        if self.config.max_prompt_length and len(prompt_text) > self.config.max_prompt_length:
            prompt_text = prompt_text[:self.config.max_prompt_length - 3] + "..."
        
        return PromptSpec(
            prompt_type=PromptType.IMAGE_TO_VIDEO,
            text=prompt_text,
            subject=subject,
            action=action,
            scene=scene_desc,
            camera=camera if self.config.include_camera_details else None,
            lighting=lighting if self.config.include_lighting else None,
            style=style if self.config.include_style else None
        )
    
    def _generate_scene_image_prompt(self, scene: Scene, report: VideoReport) -> PromptSpec:
        """Generate an image prompt for a scene without detailed shots."""
        subject = self._extract_scene_subject(scene)
        scene_desc = scene.location
        lighting = scene.lighting or "natural lighting"
        style = scene.style or report.overall_style or "cinematic, realistic"
        
        prompt_text = f"{subject} in {scene_desc}. {lighting}. {style}."
        
        return PromptSpec(
            prompt_type=PromptType.TEXT_TO_IMAGE,
            text=prompt_text,
            subject=subject,
            action="",
            scene=scene_desc,
            lighting=lighting,
            style=style,
            negative_prompt="blur, blurry, low quality"
        )
    
    def _generate_scene_video_prompt(self, scene: Scene, report: VideoReport) -> PromptSpec:
        """Generate a video prompt for a scene without detailed shots."""
        subject = self._extract_scene_subject(scene)
        action = scene.description
        scene_desc = scene.location
        lighting = scene.lighting or "natural lighting"
        style = scene.style or report.overall_style or "cinematic"
        
        prompt_text = f"{subject}. {action}. Scene: {scene_desc}. {lighting}. {style} style."
        
        return PromptSpec(
            prompt_type=PromptType.TEXT_TO_VIDEO,
            text=prompt_text,
            subject=subject,
            action=action,
            scene=scene_desc,
            lighting=lighting,
            style=style
        )
    
    def _extract_subject(self, shot: Shot, scene: Scene) -> str:
        """Extract the subject description from a shot."""
        if shot.entities:
            entity = shot.entities[0]
            if entity.appearance:
                return f"{entity.name}: {entity.appearance}"
            return entity.name
        
        if scene.key_entities:
            entity = scene.key_entities[0]
            if entity.appearance:
                return f"{entity.name}: {entity.appearance}"
            return entity.name
        
        return "Subject"
    
    def _extract_scene_subject(self, scene: Scene) -> str:
        """Extract subject from scene."""
        if scene.key_entities:
            entity = scene.key_entities[0]
            if entity.appearance:
                return f"{entity.name}: {entity.appearance}"
            return entity.name
        return "Scene"
    
    def _build_scene_description(self, scene: Scene) -> str:
        """Build a scene description."""
        parts = [scene.location]
        
        if scene.mood:
            parts.append(f"{scene.mood} atmosphere")
        
        if scene.color_palette:
            parts.append(scene.color_palette)
        
        return ", ".join(parts)
    
    def _build_camera_description(self, shot: Shot) -> str:
        """Build camera description for still image."""
        parts = []
        
        if shot.shot_type:
            parts.append(f"{shot.shot_type.value} shot")
        
        if shot.camera_description:
            parts.append(shot.camera_description)
        
        return ", ".join(parts) if parts else "medium shot"
    
    def _build_camera_movement_description(self, shot: Shot) -> str:
        """Build camera movement description for video."""
        parts = []
        
        if shot.camera_movement:
            parts.append(f"camera {shot.camera_movement.value}")
        
        if shot.camera_description:
            parts.append(shot.camera_description)
        
        return ", ".join(parts) if parts else "static camera"
    
    def _create_shot_description(self, shot: Shot, scene: Scene) -> str:
        """Create a human-readable shot description."""
        timestamp = ""
        if self.config.include_timestamps:
            timestamp = f"[{format_timestamp(shot.start_time)}-{format_timestamp(shot.end_time)}] "
        
        return f"{timestamp}Shot {shot.shot_index}: {shot.description} - {shot.action}"
    
    def _generate_notes(self, scene: Scene, report: VideoReport) -> str:
        """Generate director's notes for a scene."""
        notes_parts = []
        
        if scene.mood:
            notes_parts.append(f"Mood: {scene.mood}")
        
        if scene.lighting:
            notes_parts.append(f"Lighting: {scene.lighting}")
        
        if scene.style:
            notes_parts.append(f"Style: {scene.style}")
        
        if report.overall_mood:
            notes_parts.append(f"Overall mood: {report.overall_mood}")
        
        return ". ".join(notes_parts) if notes_parts else None
    
    @staticmethod
    def load_report(report_path: Path) -> VideoReport:
        """Load a VideoReport from disk."""
        return load_model(report_path, VideoReport)
