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
        """Generate an ultra-detailed text-to-image prompt for a shot."""
        # Core elements
        subject = self._extract_subject(shot, scene)
        action = shot.action
        scene_desc = self._build_detailed_scene_description(scene, report)
        
        # Technical cinematography
        camera = self._build_camera_description(shot)
        lens_desc = self._extract_lens_details(report, scene)
        
        # Lighting with professional terminology  
        lighting = self._build_detailed_lighting(scene, report)
        
        # Film stock and style
        film_stock = self._extract_film_stock(scene, report)
        style = self._build_comprehensive_style(scene, report)
        
        # Physical world details
        physical_details = self._extract_physical_world_details(scene)
        
        # Human subjects details
        human_details = self._extract_human_subjects_details(scene)
        
        # Texture and material details
        texture_details = self._extract_texture_details(scene)
        
        # Build comprehensive prompt
        prompt_parts = []
        
        # Subject with detailed human descriptions
        if human_details:
            prompt_parts.append(f"{subject}. {human_details}")
        else:
            prompt_parts.append(subject)
        
        # Action
        if action:
            prompt_parts.append(action)
        
        # Scene with physical world details
        scene_part = f"in {scene_desc}"
        if physical_details:
            scene_part += f". Physical environment: {physical_details}"
        prompt_parts.append(scene_part)
        
        # Camera and lens
        if self.config.include_camera_details:
            if camera:
                prompt_parts.append(f"Camera: {camera}")
            if lens_desc:
                prompt_parts.append(f"Lens: {lens_desc}")
        
        # Lighting with professional detail
        if self.config.include_lighting and lighting:
            prompt_parts.append(f"Lighting: {lighting}")
        
        # Texture and materials
        if texture_details:
            prompt_parts.append(f"Textures: {texture_details}")
        
        # Film stock and style
        if self.config.include_style:
            if film_stock:
                prompt_parts.append(f"Film stock: {film_stock}")
            if style:
                prompt_parts.append(f"Style: {style}")
        
        prompt_text = ". ".join(prompt_parts) + "."
        
        # Don't truncate - we want ALL the detail
        # if self.config.max_prompt_length and len(prompt_text) > self.config.max_prompt_length:
        #     prompt_text = prompt_text[:self.config.max_prompt_length - 3] + "..."
        
        return PromptSpec(
            prompt_type=PromptType.TEXT_TO_IMAGE,
            text=prompt_text,
            subject=subject,
            action=action,
            scene=scene_desc,
            camera=camera if self.config.include_camera_details else None,
            lighting=lighting if self.config.include_lighting else None,
            style=style if self.config.include_style else None,
            negative_prompt="blur, blurry, out of focus, distorted, low quality, pixelated, grainy artifacts, watermark, text overlay, bad anatomy, deformed"
        )
    
    def _generate_video_prompt(self, shot: Shot, scene: Scene, report: VideoReport) -> PromptSpec:
        """Generate an ultra-detailed text-to-video or image-to-video prompt for a shot."""
        subject = self._extract_subject(shot, scene)
        action = shot.action
        scene_desc = self._build_detailed_scene_description(scene, report)
        camera = self._build_camera_movement_description(shot)
        lighting = self._build_detailed_lighting(scene, report)
        film_stock = self._extract_film_stock(scene, report)
        style = self._build_comprehensive_style(scene, report)
        physical_details = self._extract_physical_world_details(scene)
        human_details = self._extract_human_subjects_details(scene)
        
        # Build comprehensive video prompt
        prompt_parts = []
        
        # Subject with human details
        if human_details:
            prompt_parts.append(f"{subject}. {human_details}")
        else:
            prompt_parts.append(subject)
        
        # Action
        if action:
            prompt_parts.append(action)
        
        # Scene with physical details
        scene_part = f"in {scene_desc}"
        if physical_details:
            scene_part += f". Environment: {physical_details}"
        prompt_parts.append(scene_part)
        
        # Camera movement
        if self.config.include_camera_details and camera:
            prompt_parts.append(f"Camera: {camera}")
        
        # Lighting
        if self.config.include_lighting and lighting:
            prompt_parts.append(f"Lighting: {lighting}")
        
        # Film stock and style
        if self.config.include_style:
            if film_stock:
                prompt_parts.append(f"Film look: {film_stock}")
            if style:
                prompt_parts.append(f"Style: {style}")
        
        prompt_text = ". ".join(prompt_parts) + "."
        
        # Don't truncate - keep all detail for accurate recreation
        # if self.config.max_prompt_length and len(prompt_text) > self.config.max_prompt_length:
        #     prompt_text = prompt_text[:self.config.max_prompt_length - 3] + "..."
        
        # Determine if first+last frame approach is beneficial
        use_first_last = self._should_use_first_last_frame(scene, shot)
        first_frame_prompt = None
        last_frame_prompt = None
        reasoning = None
        
        if use_first_last:
            first_frame_prompt, last_frame_prompt, reasoning = self._generate_first_last_frame_prompts(
                scene, shot, report
            )
        
        return PromptSpec(
            prompt_type=PromptType.IMAGE_TO_VIDEO,
            text=prompt_text,
            subject=subject,
            action=action,
            scene=scene_desc,
            camera=camera if self.config.include_camera_details else None,
            lighting=lighting if self.config.include_lighting else None,
            style=style if self.config.include_style else None,
            use_first_last_frame=use_first_last,
            first_frame_prompt=first_frame_prompt,
            last_frame_prompt=last_frame_prompt,
            first_last_frame_reasoning=reasoning
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
    
    def _build_detailed_scene_description(self, scene: Scene, report: VideoReport) -> str:
        """Build a comprehensive scene description with all environmental details."""
        parts = [scene.location]
        
        # Time and environmental context
        if scene.time_of_day:
            parts.append(scene.time_of_day)
        if scene.weather:
            parts.append(scene.weather)
        if scene.season:
            parts.append(scene.season)
        
        # Mood and atmosphere
        if scene.mood:
            parts.append(f"{scene.mood} atmosphere")
        
        # Color information
        if scene.color_palette:
            parts.append(scene.color_palette)
        if scene.color_temperature:
            parts.append(scene.color_temperature)
        
        # Cultural context
        if report.cultural_context:
            parts.append(report.cultural_context)
        
        return ", ".join(parts)
    
    def _extract_lens_details(self, report: VideoReport, scene: Scene) -> str:
        """Extract lens characteristics."""
        if report.lens_characteristics:
            return report.lens_characteristics
        return None
    
    def _build_detailed_lighting(self, scene: Scene, report: VideoReport) -> str:
        """Build comprehensive lighting description using professional terminology."""
        parts = []
        
        # Specific lighting type (from standards)
        if scene.lighting_type:
            parts.append(scene.lighting_type)
        elif scene.lighting:
            parts.append(scene.lighting)
        
        # Lighting direction
        if scene.lighting_direction:
            parts.append(f"Direction: {scene.lighting_direction}")
        
        # Color temperature
        if scene.lighting_temperature:
            parts.append(scene.lighting_temperature)
        
        return ", ".join(parts) if parts else (scene.lighting or "natural lighting")
    
    def _extract_film_stock(self, scene: Scene, report: VideoReport) -> str:
        """Extract film stock characteristics."""
        # Scene-specific film look
        if scene.film_stock_resemblance:
            return scene.film_stock_resemblance
        # Overall film look
        if report.film_stock_look:
            return report.film_stock_look
        return None
    
    def _build_comprehensive_style(self, scene: Scene, report: VideoReport) -> str:
        """Build comprehensive style description."""
        parts = []
        
        if scene.style:
            parts.append(scene.style)
        elif report.overall_style:
            parts.append(report.overall_style)
        
        if report.cultural_context and report.cultural_context not in str(scene.style):
            parts.append(report.cultural_context)
        
        return ", ".join(parts) if parts else "cinematic, realistic"
    
    def _extract_physical_world_details(self, scene: Scene) -> str:
        """Extract all physical world details - architecture, signs, vehicles, objects."""
        if not scene.physical_world:
            return None
        
        details = []
        pw = scene.physical_world
        
        # Architecture
        if "architecture" in pw and pw["architecture"]:
            arch = pw["architecture"]
            if isinstance(arch, list):
                details.append(f"Architecture: {', '.join(str(a) for a in arch)}")
            else:
                details.append(f"Architecture: {arch}")
        
        # Signs and text
        if "signs_text" in pw and pw["signs_text"]:
            signs = pw["signs_text"]
            if isinstance(signs, list):
                sign_strs = []
                for sign in signs:
                    if isinstance(sign, dict):
                        content = sign.get('content', '')
                        lang = sign.get('language', '')
                        sign_type = sign.get('type', '')
                        sign_strs.append(f"'{content}' ({lang}, {sign_type})" if lang and sign_type else content)
                    else:
                        sign_strs.append(str(sign))
                if sign_strs:
                    details.append(f"Signage: {'; '.join(sign_strs)}")
            else:
                details.append(f"Signage: {signs}")
        
        # Vehicles
        if "vehicles" in pw and pw["vehicles"]:
            vehicles = pw["vehicles"]
            if isinstance(vehicles, list):
                vehicle_strs = []
                for vehicle in vehicles:
                    if isinstance(vehicle, dict):
                        make = vehicle.get('make_model_estimate', vehicle.get('type', ''))
                        color = vehicle.get('color', '')
                        position = vehicle.get('position', '')
                        vehicle_strs.append(f"{color} {make} {position}" if color and position else f"{color} {make}" if color else make)
                    else:
                        vehicle_strs.append(str(vehicle))
                if vehicle_strs:
                    details.append(f"Vehicles: {', '.join(vehicle_strs)}")
            else:
                details.append(f"Vehicles: {vehicles}")
        
        # Objects
        if "objects" in pw and pw["objects"]:
            objects = pw["objects"]
            if isinstance(objects, str):
                details.append(f"Objects: {objects}")
            elif isinstance(objects, list):
                details.append(f"Objects: {', '.join(str(o) for o in objects)}")
        
        # Infrastructure
        if "infrastructure" in pw and pw["infrastructure"]:
            infra = pw["infrastructure"]
            if isinstance(infra, str):
                details.append(f"Infrastructure: {infra}")
            elif isinstance(infra, list):
                details.append(f"Infrastructure: {', '.join(str(i) for i in infra)}")
        
        return "; ".join(details) if details else None
    
    def _extract_human_subjects_details(self, scene: Scene) -> str:
        """Extract detailed human subject information."""
        if not scene.human_subjects:
            return None
        
        details = []
        for subject in scene.human_subjects:
            if isinstance(subject, dict):
                parts = []
                
                # Count and position
                if "count" in subject:
                    parts.append(f"{subject['count']} person(s)")
                if "position" in subject:
                    parts.append(f"positioned {subject['position']}")
                
                # Demographics
                if "demographics" in subject:
                    parts.append(subject["demographics"])
                
                # Physical description
                if "physical_description" in subject:
                    parts.append(subject["physical_description"])
                
                # Clothing
                if "clothing" in subject:
                    parts.append(f"wearing {subject['clothing']}")
                
                # Body language
                if "body_language" in subject:
                    parts.append(f"with {subject['body_language']}")
                
                if parts:
                    details.append(", ".join(parts))
        
        return "; ".join(details) if details else None
    
    def _extract_texture_details(self, scene: Scene) -> str:
        """Extract texture and material details."""
        if not scene.texture_details:
            return None
        
        textures = scene.texture_details
        if isinstance(textures, dict):
            parts = []
            for material, description in textures.items():
                parts.append(f"{material}: {description}")
            return ", ".join(parts)
        elif isinstance(textures, str):
            return textures
        
        return None
    
    def _should_use_first_last_frame(self, scene: Scene, shot: Shot) -> bool:
        """
        Determine if this scene/shot should use Kling 2.1 Pro's first+last frame approach.
        
        Returns True if first+last frame is recommended based on:
        - Scene duration (longer scenes benefit more)
        - Amount of movement/transformation
        - Complexity of action
        - Clear beginning and end states
        """
        # Don't use for very short scenes (less than 2 seconds)
        if scene.duration < 2.0:
            return False
        
        # Check for significant movement indicators in action description
        action = shot.action.lower() if shot.action else ""
        description = shot.description.lower() if shot.description else ""
        
        # Keywords that suggest significant transformation/movement
        movement_keywords = [
            'walk', 'run', 'move', 'approach', 'exit', 'enter', 'turn',
            'lean', 'ride', 'drive', 'fly', 'jump', 'fall', 'rise',
            'transform', 'change', 'transition', 'travel', 'cross'
        ]
        
        # Check if scene has significant movement
        has_movement = any(keyword in action or keyword in description for keyword in movement_keywords)
        
        # Check camera movement (tracking, dolly, crane, etc. benefit from first+last)
        camera_movement = shot.camera_movement.lower() if shot.camera_movement else ""
        has_camera_movement = any(mv in camera_movement for mv in ['track', 'dolly', 'crane', 'follow', 'orbit'])
        
        # Use first+last frame if:
        # 1. Scene is longer than 2 seconds AND has movement/transformation
        # 2. OR scene is longer than 4 seconds (even without obvious movement, provides better control)
        # 3. OR has significant camera movement
        
        if scene.duration >= 4.0:
            return True
        
        if scene.duration >= 2.0 and (has_movement or has_camera_movement):
            return True
        
        return False
    
    def _generate_first_last_frame_prompts(self, scene: Scene, shot: Shot, report: VideoReport) -> tuple[str, str, str]:
        """
        Generate first frame and last frame prompts for Kling 2.1 Pro.
        
        Returns:
            tuple: (first_frame_prompt, last_frame_prompt, reasoning)
        """
        # Extract base elements
        subject = self._extract_subject(shot, scene)
        scene_desc = self._build_detailed_scene_description(scene, report)
        lighting = self._build_detailed_lighting(scene, report)
        film_stock = self._extract_film_stock(scene, report)
        style = self._build_comprehensive_style(scene, report)
        
        # Build base prompt elements
        base_elements = []
        base_elements.append(f"in {scene_desc}")
        if lighting:
            base_elements.append(f"Lighting: {lighting}")
        if film_stock:
            base_elements.append(f"Film: {film_stock}")
        if style:
            base_elements.append(f"Style: {style}")
        
        base_prompt = ". ".join(base_elements)
        
        # Analyze action to determine first vs last frame states
        action = shot.action if shot.action else ""
        
        # FIRST FRAME: Beginning state
        # Extract starting position/state from camera position or spatial relationships
        first_frame_subject = subject
        if shot.camera_position and "starts at" in shot.camera_position.lower():
            # Extract starting position info
            first_frame_subject += " at starting position"
        
        first_frame_prompt = f"{first_frame_subject}. {base_prompt}. Beginning of action."
        
        # LAST FRAME: Ending state  
        # Try to infer end state from action description
        last_frame_subject = subject
        if "toward" in action.lower():
            last_frame_subject += " having moved closer"
        elif "away" in action.lower():
            last_frame_subject += " having moved away"
        elif "turn" in action.lower():
            last_frame_subject += " turned"
        elif "exit" in action.lower() or "leave" in action.lower():
            last_frame_subject += " at exit point"
        elif "enter" in action.lower():
            last_frame_subject += " having entered"
        else:
            last_frame_subject += " at end of movement"
        
        last_frame_prompt = f"{last_frame_subject}. {base_prompt}. End of action."
        
        # Generate reasoning
        duration_reason = f"Scene duration is {scene.duration:.1f}s"
        movement_reason = "Scene has significant movement/transformation" if any(kw in action.lower() for kw in ['walk', 'move', 'turn', 'ride']) else "Scene has camera movement"
        
        reasoning = f"{duration_reason}, {movement_reason}. First+last frame approach provides better control over start and end states for Kling 2.1 Pro video generation."
        
        return (first_frame_prompt, last_frame_prompt, reasoning)
    
    def _build_camera_description(self, shot: Shot) -> str:
        """Build camera description for still image."""
        parts = []
        
        if shot.shot_type:
            shot_type_str = shot.shot_type if isinstance(shot.shot_type, str) else shot.shot_type.value
            parts.append(f"{shot_type_str} shot")
        
        if shot.camera_description:
            parts.append(shot.camera_description)
        
        return ", ".join(parts) if parts else "medium shot"
    
    def _build_camera_movement_description(self, shot: Shot) -> str:
        """Build camera movement description for video."""
        parts = []
        
        if shot.camera_movement:
            movement_str = shot.camera_movement if isinstance(shot.camera_movement, str) else shot.camera_movement.value
            parts.append(f"camera {movement_str}")
        
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
