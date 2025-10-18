"""Prompt Generation Agent - Converts video analysis into generation prompts."""

import re

from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

from ..models import (
    VideoReport, Scene, Shot, Entity,
    PromptSpec, PromptBundle, PromptType,
    CameraShotBreakdown,
)
from ..paths import path_builder
from ..storage import save_model, load_model
from ..settings import settings
from ..logging import get_logger, LogContext
from ..utils import format_timestamp
from .camera_analysis import CameraVisionAnalyzer

logger = get_logger(__name__)

SHOT_TYPE_MAP = {
    "extreme_close_up": "Extreme close-up",
    "extreme close up": "Extreme close-up",
    "extreme_closeup": "Extreme close-up",
    "close_up": "Close-up",
    "close up": "Close-up",
    "medium_close_up": "Medium close-up",
    "medium close up": "Medium close-up",
    "medium_shot": "Medium shot",
    "medium": "Medium shot",
    "full_body": "Full body shot",
    "full shot": "Full body shot",
    "wide": "Wide shot",
    "wide_shot": "Wide shot",
    "long": "Long shot",
    "long_shot": "Long shot",
    "establishing": "Wide establishing shot",
    "two_shot": "Two-shot",
    "over_shoulder": "Over-the-shoulder shot",
    "pov": "Point-of-view shot",
}

MOVEMENT_PHRASES = {
    "tracking": "tracking camera move",
    "dolly": "dolly move",
    "zoom in": "slow zoom-in",
    "zoom out": "slow zoom-out",
    "pan left": "leftward pan",
    "pan right": "rightward pan",
    "tilt up": "tilt-up move",
    "tilt down": "tilt-down move",
    "orbit": "orbiting move",
    "handheld": "handheld camera energy",
    "crane": "crane move",
    "roll": "rolling move",
}

class PromptGenerationAgent:
    """Agent for generating prompts from video analysis."""
    
    def __init__(self):
        self.config = settings.prompts
        self.camera_analyzer = CameraVisionAnalyzer()
    
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

        camera_breakdowns = self._ensure_camera_breakdowns(scene, report)

        for idx, shot in enumerate(scene.shots):
            breakdown = camera_breakdowns[idx] if idx < len(camera_breakdowns) else None

            if self._is_montage_shot(scene, shot):
                clip_labels = self._extract_montage_items(scene, shot)
                base_description = self._create_shot_description(shot, scene, breakdown)
                if clip_labels:
                    shot_descriptions.append(base_description + " [Montage overview]")
                    for clip_idx, clip_label in enumerate(clip_labels, 1):
                        img_prompt = self._generate_image_prompt(
                            shot,
                            scene,
                            report,
                            breakdown,
                            clip_label=clip_label,
                            clip_index=clip_idx,
                        )
                        image_prompts.append(img_prompt)

                        vid_prompt = self._generate_video_prompt(
                            shot,
                            scene,
                            report,
                            breakdown,
                            clip_label=clip_label,
                        )
                        video_prompts.append(vid_prompt)

                        clip_description = self._create_montage_clip_description(
                            shot,
                            scene,
                            breakdown,
                            clip_label,
                            clip_idx,
                        )
                        shot_descriptions.append(clip_description)
                    continue
                else:
                    # Fall back to standard handling if we couldn't extract clips.
                    shot_descriptions.append(base_description)

            img_prompt = self._generate_image_prompt(shot, scene, report, breakdown)
            image_prompts.append(img_prompt)

            vid_prompt = self._generate_video_prompt(shot, scene, report, breakdown)
            video_prompts.append(vid_prompt)

            shot_desc = self._create_shot_description(shot, scene, breakdown)
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
            camera_breakdowns=camera_breakdowns,
            created_at=datetime.now()
        )
        
        return bundle
    
    def _ensure_camera_breakdowns(self, scene: Scene, report: VideoReport) -> list[CameraShotBreakdown]:
        """Ensure camera breakdowns are available for a scene."""

        breakdowns = self.camera_analyzer.analyze_scene(scene, report)
        scene.camera_breakdowns = breakdowns
        return breakdowns

    def _generate_image_prompt(
        self,
        shot: Shot,
        scene: Scene,
        report: VideoReport,
        breakdown: Optional[CameraShotBreakdown] = None,
        clip_label: Optional[str] = None,
        clip_index: Optional[int] = None,
    ) -> PromptSpec:
        """Generate an ultra-detailed text-to-image prompt for a shot."""
        # Core elements
        clip_subject, clip_action = self._clip_phrases(clip_label, shot.action)

        subject = clip_subject or self._extract_subject(shot, scene)
        action = clip_action or shot.action
        scene_desc = self._build_detailed_scene_description(scene, report)

        # Technical cinematography and lighting
        camera = self._compose_camera_prompt(shot, breakdown)
        lens_desc = self._extract_lens_details(scene, breakdown)
        if lens_desc and camera and lens_desc.lower() in camera.lower():
            lens_desc = None
        lighting = self._compose_lighting_prompt(scene, report, breakdown)
        recreation_guidance = breakdown.recreation_guidance if breakdown else None
        composition_notes = breakdown.composition_notes if breakdown else None
        set_design_notes = breakdown.set_design_notes if breakdown else None
        
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
        if clip_subject and not physical_details:
            scene_part += f". Clip focus: {clip_subject}"
        prompt_parts.append(scene_part)
        
        # Camera and lens
        if self.config.include_camera_details:
            if camera:
                prompt_parts.append(f"Camera: {camera}")
            if lens_desc:
                prompt_parts.append(f"Lens: {lens_desc}")
            if composition_notes and composition_notes.lower() not in " ".join(prompt_parts).lower():
                prompt_parts.append(f"Composition: {composition_notes}")
            if set_design_notes and set_design_notes.lower() not in " ".join(prompt_parts).lower():
                prompt_parts.append(f"Set design: {set_design_notes}")

        # Lighting with professional detail
        if self.config.include_lighting and lighting:
            prompt_parts.append(f"Lighting: {lighting}")

        if recreation_guidance:
            prompt_parts.append(f"Recreation guidance: {recreation_guidance}")
        
        # Texture and materials
        if texture_details:
            prompt_parts.append(f"Textures: {texture_details}")
        
        # Film stock and style
        if self.config.include_style and style:
            prompt_parts.append(f"Style: {style}")
        
        prompt_parts = self._unique_parts(prompt_parts)
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
    
    def _generate_video_prompt(
        self,
        shot: Shot,
        scene: Scene,
        report: VideoReport,
        breakdown: Optional[CameraShotBreakdown] = None,
        clip_label: Optional[str] = None,
    ) -> PromptSpec:
        """Generate an ultra-detailed text-to-video or image-to-video prompt for a shot."""
        clip_subject, clip_action = self._clip_phrases(clip_label, shot.action)

        subject = clip_subject or self._extract_subject(shot, scene)
        action = clip_action or shot.action
        scene_desc = self._build_detailed_scene_description(scene, report)
        camera = self._compose_camera_prompt(shot, breakdown)
        lighting = self._compose_lighting_prompt(scene, report, breakdown)
        style = self._build_comprehensive_style(scene, report)
        physical_details = self._extract_physical_world_details(scene)
        human_details = self._extract_human_subjects_details(scene)
        recreation_guidance = breakdown.recreation_guidance if breakdown else None
        cinematic_purpose = breakdown.cinematic_purpose if breakdown else None

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
        if clip_subject and not physical_details:
            scene_part += f". Clip focus: {clip_subject}"
        prompt_parts.append(scene_part)

        # Camera and movement
        if self.config.include_camera_details and camera:
            prompt_parts.append(f"Camera: {camera}")

        # Lighting
        if self.config.include_lighting and lighting:
            prompt_parts.append(f"Lighting: {lighting}")

        if cinematic_purpose:
            prompt_parts.append(f"Purpose: {cinematic_purpose}")

        if recreation_guidance:
            prompt_parts.append(f"Recreation guidance: {recreation_guidance}")

        # Film stock and style
        if self.config.include_style and style:
            prompt_parts.append(f"Style: {style}")

        prompt_parts = self._unique_parts(prompt_parts)
        prompt_text = ". ".join(prompt_parts) + "."

        # Determine if first+last frame approach is beneficial
        use_first_last = self._should_use_first_last_frame(scene, shot)
        if clip_label:
            use_first_last = False
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
            first_last_frame_reasoning=reasoning,
        )
    
    def _generate_scene_image_prompt(self, scene: Scene, report: VideoReport) -> PromptSpec:
        """Generate an image prompt for a scene without detailed shots."""
        subject = self._extract_scene_subject(scene)
        scene_desc = scene.location
        lighting = scene.lighting or "natural lighting"
        style = scene.style or scene.mood or "cinematic, realistic"
        
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
        style = scene.style or scene.mood or "cinematic"
        
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
        
        if scene.human_subjects:
            return self._summarize_human_subject(scene.human_subjects[0])
        
        return "Primary subject"
    
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

        return ", ".join(parts)

    def _extract_lens_details(
        self,
        scene: Scene,
        breakdown: Optional[CameraShotBreakdown],
    ) -> Optional[str]:
        """Extract lens characteristics specific to a scene or shot."""

        if breakdown and breakdown.lens_type_estimate:
            return breakdown.lens_type_estimate

        for shot in scene.shots:
            if shot.lens_focal_length:
                return str(shot.lens_focal_length)

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
    
    def _build_comprehensive_style(self, scene: Scene, report: VideoReport) -> str:
        """Build comprehensive style description."""
        parts = []

        if scene.style:
            parts.append(scene.style)
        if scene.mood:
            parts.append(scene.mood)

        return ", ".join(parts) if parts else "cinematic, realistic"
    
    def _extract_physical_world_details(self, scene: Scene) -> str:
        """Extract all physical world details - architecture, signs, vehicles, objects."""
        if not scene.physical_world:
            return None
        
        pw = scene.physical_world
        sections = []
        
        architecture = pw.get("architecture")
        if architecture:
            arch_items = architecture if isinstance(architecture, list) else [architecture]
            arch_descriptions = [self._describe_architecture(item) for item in arch_items]
            arch_descriptions = [d for d in arch_descriptions if d]
            if arch_descriptions:
                sections.append("Architecture: " + "; ".join(arch_descriptions))
        
        signage = pw.get("signs_text") or pw.get("signs") or pw.get("signage")
        if signage:
            sign_items = signage if isinstance(signage, list) else [signage]
            sign_descriptions = [self._describe_sign(item) for item in sign_items]
            sign_descriptions = [d for d in sign_descriptions if d]
            if sign_descriptions:
                sections.append("Signage: " + "; ".join(sign_descriptions))
        
        vehicles = pw.get("vehicles")
        if vehicles:
            vehicle_items = vehicles if isinstance(vehicles, list) else [vehicles]
            vehicle_descriptions = [self._describe_vehicle(item) for item in vehicle_items]
            vehicle_descriptions = [d for d in vehicle_descriptions if d]
            if vehicle_descriptions:
                sections.append("Vehicles: " + "; ".join(vehicle_descriptions))
        
        objects = pw.get("objects") or pw.get("props")
        if objects:
            object_items = objects if isinstance(objects, list) else [objects]
            object_descriptions = [self._describe_object(item) for item in object_items]
            object_descriptions = [d for d in object_descriptions if d]
            if object_descriptions:
                sections.append("Objects: " + "; ".join(object_descriptions))
        
        infrastructure = pw.get("infrastructure")
        if infrastructure:
            infra_items = infrastructure if isinstance(infrastructure, list) else [infrastructure]
            infra_descriptions = [self._describe_infrastructure(item) for item in infra_items]
            infra_descriptions = [d for d in infra_descriptions if d]
            if infra_descriptions:
                sections.append("Infrastructure: " + "; ".join(infra_descriptions))
        
        vegetation = pw.get("vegetation")
        if vegetation:
            veg_items = vegetation if isinstance(vegetation, list) else [vegetation]
            veg_descriptions = [self._clean_text(item) for item in veg_items if item]
            veg_descriptions = [d for d in veg_descriptions if d]
            if veg_descriptions:
                sections.append("Vegetation: " + "; ".join(veg_descriptions))
        
        return " ".join(sections) if sections else None
    
    def _extract_human_subjects_details(self, scene: Scene) -> str:
        """Extract detailed human subject information."""
        if not scene.human_subjects:
            return None
        
        descriptions = []
        for subject in scene.human_subjects:
            desc = self._describe_human_subject(subject)
            if desc:
                descriptions.append(desc)
        
        return "; ".join(descriptions) if descriptions else None
    
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

    def _clean_text(self, value) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        if text.endswith("."):
            text = text[:-1]
        return text

    def _describe_architecture(self, item) -> Optional[str]:
        if not item:
            return None
        if not isinstance(item, dict):
            return self._clean_text(item)
        label = item.get("id") or item.get("name")
        core_parts = []
        for key in ["type", "style", "materials", "condition", "height"]:
            value = self._clean_text(item.get(key))
            if value:
                if key == "height":
                    core_parts.append(f"height {value}")
                else:
                    core_parts.append(value)
        position_parts = []
        for key in ["position_relative_to_subject", "position_relative_to_camera", "orientation"]:
            value = self._clean_text(item.get(key))
            if value:
                position_parts.append(value)
        if position_parts:
            core_parts.append("; ".join(position_parts))
        description = ", ".join([part for part in core_parts if part])
        if label:
            label_text = self._clean_text(label).replace("_", " ")
            return f"{label_text}: {description}" if description else label_text
        return description

    def _describe_sign(self, item) -> Optional[str]:
        if not item:
            return None
        if not isinstance(item, dict):
            return self._clean_text(item)
        text = self._clean_text(item.get("text") or item.get("content"))
        translation = self._clean_text(item.get("translation"))
        sign_type = self._clean_text(item.get("type"))
        language = self._clean_text(item.get("language"))
        colors = self._clean_text(item.get("colors"))
        lighting = self._clean_text(item.get("lighting"))
        location = self._clean_text(item.get("location"))
        brand = self._clean_text(item.get("brand"))
        parts = []
        if text:
            if translation and translation.lower() != text.lower():
                parts.append(f"\"{text}\" ({translation})")
            else:
                parts.append(f"\"{text}\"")
        if brand and brand.lower() not in text.lower():
            parts.append(f"brand {brand}")
        if sign_type:
            parts.append(sign_type)
        if language:
            parts.append(f"language: {language}")
        if colors:
            parts.append(f"colors {colors}")
        if lighting:
            parts.append(f"lighting {lighting}")
        if location:
            parts.append(f"located {location}")
        return ", ".join([p for p in parts if p])

    def _describe_vehicle(self, item) -> Optional[str]:
        if not item:
            return None
        if not isinstance(item, dict):
            return self._clean_text(item)
        color = self._clean_text(item.get("color"))
        make_model = self._clean_text(item.get("make_model") or item.get("make_model_estimate") or item.get("model") or item.get("model_guess"))
        vehicle_type = self._clean_text(item.get("type"))
        brand = self._clean_text(item.get("brand"))
        year = self._clean_text(item.get("year") or item.get("generation"))
        condition = self._clean_text(item.get("condition"))
        position = self._clean_text(item.get("position"))
        distance = self._clean_text(item.get("distance_from_camera"))
        motion = self._clean_text(item.get("movement"))
        license_plate = self._clean_text(item.get("license_plate"))
        parts = []
        descriptor = ""
        if color:
            descriptor += color + " "
        if brand and (not make_model or brand.lower() not in make_model.lower()):
            descriptor += brand + " "
        if make_model:
            descriptor += make_model
        elif vehicle_type:
            descriptor += vehicle_type
        descriptor = descriptor.strip()
        if descriptor:
            parts.append(descriptor)
        elif vehicle_type:
            parts.append(vehicle_type)
        if year:
            parts.append(year)
        if condition:
            parts.append(condition)
        if position:
            parts.append(position)
        if distance:
            parts.append(f"approximately {distance}")
        if motion:
            parts.append(motion)
        if license_plate:
            parts.append(f"license plate {license_plate}")
        return ", ".join([p for p in parts if p])

    def _describe_object(self, item) -> Optional[str]:
        if not item:
            return None
        if isinstance(item, str):
            return self._clean_text(item)
        if isinstance(item, dict):
            obj_type = self._clean_text(item.get("type") or item.get("name"))
            brand = self._clean_text(item.get("brand"))
            make_model = self._clean_text(item.get("make_model") or item.get("make") or item.get("model"))
            description = self._clean_text(item.get("description"))
            position = self._clean_text(item.get("position"))
            color = self._clean_text(item.get("color"))
            quantity = self._clean_text(item.get("count") or item.get("quantity"))
            parts = []
            label = obj_type or "object"
            if brand and brand.lower() not in label.lower():
                label = f"{brand} {label}".strip()
            if make_model and make_model.lower() not in label.lower():
                label = f"{label} ({make_model})"
            if color:
                label = f"{color} {label}".strip()
            parts.append(label)
            if quantity:
                parts.append(f"quantity: {quantity}")
            if description:
                parts.append(description)
            if position:
                parts.append(position)
            return ", ".join([p for p in parts if p])
        return None

    def _describe_infrastructure(self, item) -> Optional[str]:
        if not item:
            return None
        if isinstance(item, dict):
            desc_parts = []
            for key, value in item.items():
                clean_val = self._clean_text(value)
                if clean_val:
                    desc_parts.append(f"{key}: {clean_val}")
            return ", ".join(desc_parts)
        return self._clean_text(item)

    def _describe_human_subject(self, subject) -> Optional[str]:
        """Extract COMPLETE human subject description including all available fields."""
        if not subject:
            return None
        if not isinstance(subject, dict):
            return self._clean_text(subject)
        
        parts = []
        
        # Core identity
        identity = self._format_demographics(subject.get("count"), subject.get("demographics"))
        physical = self._format_physical_description(subject.get("physical_description"))
        if identity and physical:
            parts.append(f"{identity} ({physical})")
        elif identity:
            parts.append(identity)
        elif physical:
            parts.append(physical)
        
        # Position (with START/END states)
        position = self._format_position(subject.get("position") or subject.get("position_in_frame"))
        if position:
            parts.append(position)
        
        # Clothing (COMPLETE inventory)
        clothing = self._format_clothing(subject.get("clothing"))
        if clothing:
            parts.append(f"wearing {clothing}")
        
        # Surface
        surface = self._clean_text(subject.get("surface_on") or (subject.get("position", {}).get("surface") if isinstance(subject.get("position"), dict) else None))
        if surface:
            parts.append(f"on {surface}")
        
        # Action and movement
        action = self._clean_text(subject.get("action"))
        if action:
            parts.append(action)
        
        # Body language and posture
        body_language = self._clean_text(subject.get("body_language"))
        if body_language:
            parts.append(body_language)
        
        # Movement physics (hair, clothing movement, shadows)
        physics = self._format_physics(subject.get("physics") or subject.get("movement_physics"))
        if physics:
            parts.append(f"physics: {physics}")
        
        # Body positioning & physical interactions with other subjects
        interaction = self._clean_text(subject.get("physical_interaction") or subject.get("body_positioning"))
        if interaction:
            parts.append(f"interaction: {interaction}")
        
        # Transformation description (for first+last frame)
        transform = self._clean_text(subject.get("transformation_description"))
        if transform:
            parts.append(f"movement: {transform}")
        
        return "; ".join([p for p in parts if p])

    def _format_demographics(self, count, demographics) -> Optional[str]:
        count_text = None
        if isinstance(count, (int, float)):
            if count > 1:
                count_text = f"{int(count)} people"
        elif count:
            count_text = self._clean_text(count)
        if isinstance(demographics, dict):
            demo_parts = []
            age = self._clean_text(demographics.get("age_group"))
            gender = self._clean_text(demographics.get("gender_presentation"))
            ethnicity = self._clean_text(demographics.get("ethnicity"))
            if age:
                demo_parts.append(age)
            if gender:
                demo_parts.append(gender)
            if ethnicity:
                demo_parts.append(ethnicity)
            demo_text = " ".join(demo_parts)
        else:
            demo_text = self._clean_text(demographics)
        if count_text and demo_text:
            return f"{count_text} {demo_text}"
        return demo_text or count_text

    def _format_physical_description(self, physical) -> Optional[str]:
        if isinstance(physical, dict):
            parts = []
            for key in ["height", "build", "hair", "skin_tone", "facial_hair", "facial_features"]:
                value = self._clean_text(physical.get(key))
                if value:
                    parts.append(value)
            return ", ".join(parts)
        return self._clean_text(physical)

    def _format_clothing(self, clothing) -> Optional[str]:
        if isinstance(clothing, dict):
            order = ["upper_body", "mid_layer", "outer_layer", "lower_body", "footwear", "accessories", "headwear"]
            parts = []
            for key in order:
                value = clothing.get(key)
                if value:
                    parts.append(self._clean_text(value))
            return "; ".join(parts)
        return self._clean_text(clothing)

    def _format_position(self, position) -> Optional[str]:
        """Format position with START/END states for first+last frame generation."""
        if isinstance(position, dict):
            start = self._clean_text(position.get("start_state"))
            end = self._clean_text(position.get("end_state"))
            transform = self._clean_text(position.get("transformation_description"))
            surface = self._clean_text(position.get("surface"))
            parts = []
            
            # If we have both start and end states (for first+last frame)
            if start and end and start != end:
                parts.append(f"STARTS: {start}")
                parts.append(f"ENDS: {end}")
                if transform:
                    parts.append(f"MOVEMENT: {transform}")
            elif start:
                parts.append(f"positioned {start}")
            elif end:
                parts.append(f"positioned {end}")
            
            if surface:
                parts.append(f"on {surface}")
            
            return "; ".join(parts)
        return self._clean_text(position)

    def _format_physics(self, physics) -> Optional[str]:
        if isinstance(physics, dict):
            parts = []
            for key, value in physics.items():
                clean_val = self._clean_text(value)
                if clean_val:
                    parts.append(f"{key}: {clean_val}")
            return "; ".join(parts)
        return self._clean_text(physics)

    def _summarize_human_subject(self, subject) -> str:
        if not isinstance(subject, dict):
            return self._clean_text(subject) or "Primary subject"
        identity = self._format_demographics(subject.get("count"), subject.get("demographics"))
        physical = self._format_physical_description(subject.get("physical_description"))
        clothing = subject.get("clothing")
        clothing_summary = None
        if isinstance(clothing, dict):
            upper = self._clean_text(clothing.get("upper_body"))
            lower = self._clean_text(clothing.get("lower_body"))
            footwear = self._clean_text(clothing.get("footwear"))
            pieces = [p for p in [upper, lower, footwear] if p]
            if pieces:
                clothing_summary = ", ".join(pieces)
        else:
            clothing_summary = self._clean_text(clothing)
        summary_parts = []
        if identity:
            summary_parts.append(identity)
        elif physical:
            summary_parts.append(physical)
        if clothing_summary:
            summary_parts.append(f"wearing {clothing_summary}")
        return " ".join(summary_parts) if summary_parts else (physical or "Primary subject")
    
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
        style = self._build_comprehensive_style(scene, report)
        
        # Build base prompt elements
        base_elements = []
        base_elements.append(f"in {scene_desc}")
        if lighting:
            base_elements.append(f"Lighting: {lighting}")
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
    
    def _compose_camera_prompt(
        self,
        shot: Shot,
        breakdown: Optional[CameraShotBreakdown],
    ) -> Optional[str]:
        """Compose a concise camera description using derived breakdown data."""

        parts: list[str] = []

        if breakdown:
            if breakdown.camera_shot_type:
                parts.append(breakdown.camera_shot_type)
            if breakdown.camera_angle:
                parts.append(f"{breakdown.camera_angle} angle")
            if breakdown.camera_height:
                parts.append(breakdown.camera_height)
            if breakdown.camera_distance:
                parts.append(breakdown.camera_distance)
            if breakdown.framing_style:
                framing = breakdown.framing_style
                if "composition" not in framing.lower():
                    framing += " composition"
                parts.append(framing)
            if breakdown.lens_type_estimate:
                lens = breakdown.lens_type_estimate.strip()
                if lens and "indeterminate" not in lens.lower():
                    if "lens" not in lens.lower():
                        lens += " lens"
                    parts.append(lens)
            if breakdown.depth_of_field:
                dof = breakdown.depth_of_field
                if "indeterminate" in dof.lower():
                    parts.append(dof)
                else:
                    if "depth of field" not in dof.lower() and "focus" not in dof.lower():
                        dof += " depth of field"
                    parts.append(dof)
            movement_phrase = self._movement_phrase(breakdown.camera_motion)
            if movement_phrase:
                parts.append(movement_phrase)
        else:
            shot_type_str = self._humanize_shot_type(shot.shot_type)
            if shot_type_str:
                parts.append(shot_type_str)
            if shot.camera_description:
                parts.append(shot.camera_description)
            movement_phrase = self._movement_phrase(shot.camera_movement)
            if movement_phrase:
                parts.append(movement_phrase)

        parts = self._unique_parts(parts)
        if not parts:
            return None

        return ", ".join(parts)

    def _compose_lighting_prompt(
        self,
        scene: Scene,
        report: VideoReport,
        breakdown: Optional[CameraShotBreakdown],
    ) -> Optional[str]:
        """Merge scene lighting details with derived lighting breakdown."""

        base_lighting = self._build_detailed_lighting(scene, report)
        parts: list[str] = [base_lighting] if base_lighting else []

        if breakdown and breakdown.lighting_style:
            lighting_style = breakdown.lighting_style
            extra_bits: list[str] = []
            if lighting_style.key_light:
                extra_bits.append(f"Key: {lighting_style.key_light}")
            if lighting_style.fill_light:
                extra_bits.append(f"Fill: {lighting_style.fill_light}")
            if lighting_style.practical_lights:
                extra_bits.append(f"Practicals: {lighting_style.practical_lights}")
            if lighting_style.mood and (not base_lighting or lighting_style.mood.lower() not in base_lighting.lower()):
                extra_bits.append(f"Mood: {lighting_style.mood}")
            if extra_bits:
                parts.append("; ".join(extra_bits))

        parts = self._unique_parts(parts)
        if not parts:
            return None

        return ". ".join(parts)

    def _unique_parts(self, parts: list[Optional[str]]) -> list[str]:
        """Return case-insensitive unique strings preserving order."""

        unique: list[str] = []
        seen: set[str] = set()
        for part in parts:
            if not part:
                continue
            normalized = part.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(part.strip())
        return unique

    def _humanize_shot_type(self, shot_type: Optional[str]) -> Optional[str]:
        if not shot_type:
            return None
        key = shot_type.lower().strip()
        if key in SHOT_TYPE_MAP:
            return SHOT_TYPE_MAP[key]
        label = shot_type.replace("_", " ").strip(" .")
        if not label:
            return None
        if ":" in label or "shot" in label.lower():
            return label
        label = label.title()
        if not label.lower().endswith("shot"):
            label += " Shot"
        return label

    def _movement_phrase(self, movement: Optional[str]) -> Optional[str]:
        if not movement:
            return None
        normalized = movement.lower().replace("_", " ").strip()
        if not normalized or normalized == "static":
            return None
        return MOVEMENT_PHRASES.get(normalized, f"{normalized} move")

    def _is_montage_shot(self, scene: Scene, shot: Shot) -> bool:
        text_parts = [scene.description, shot.description, shot.action]
        combined = " ".join(filter(None, text_parts)).lower()
        if "montage" in combined:
            return True
        if shot.duration is not None and shot.duration <= 0.75 and "clips" in combined:
            return True
        return False

    def _extract_montage_items(self, scene: Scene, shot: Shot) -> list[str]:
        candidates: list[str] = []
        text_sources = [scene.description, shot.description, shot.action]
        for text in filter(None, text_sources):
            candidates.extend(self._parse_montage_clause(text))
            candidates.extend(self._extract_parenthetical_items(text))

        if not candidates and scene.physical_world:
            objects = scene.physical_world.get("objects") if isinstance(scene.physical_world, dict) else None
            if isinstance(objects, list):
                candidates.extend(objects)

        return self._dedupe_clip_labels(candidates)

    def _parse_montage_clause(self, text: str) -> list[str]:
        matches: list[str] = []
        pattern = re.compile(r"(?:clips? include|including|includes|features|featuring|showcasing)\s+([^\.]+)", re.IGNORECASE)
        for match in pattern.finditer(text):
            clause = match.group(1)
            clause = re.split(r"(?i)(?:each clip|each moment|each shot)", clause)[0]
            clause = clause.replace(" and ", ", ")
            parts = [part.strip() for part in clause.split(",") if part.strip()]
            matches.extend(parts)
        return matches

    def _extract_parenthetical_items(self, text: str) -> list[str]:
        items: list[str] = []
        for match in re.finditer(r"\(([^\)]+)\)", text):
            segment = match.group(1)
            if any(sep in segment for sep in [",", "/", ";"]):
                segment = segment.replace(" and ", ", ")
                items.extend([part.strip() for part in segment.split(",") if part.strip()])
        return items

    def _clean_clip_label(self, label: str) -> Optional[str]:
        cleaned = re.sub(r"\s+", " ", str(label)).strip().strip(".;:")
        return cleaned or None

    def _dedupe_clip_labels(self, labels: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for label in labels:
            cleaned = self._clean_clip_label(label)
            if not cleaned:
                continue
            key = re.sub(r"^(a|an|the)\s+", "", cleaned, flags=re.IGNORECASE).lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(cleaned)
        return result

    def _clip_phrases(self, clip_label: Optional[str], fallback_action: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if not clip_label:
            return None, None
        cleaned = self._clean_clip_label(clip_label)
        if not cleaned:
            return None, None
        subject = cleaned[0].upper() + cleaned[1:] if cleaned else cleaned
        if fallback_action and "montage" not in fallback_action.lower():
            action = fallback_action
        else:
            action = f"{subject} captured at peak intensity"
        return subject, action

    def _create_montage_clip_description(
        self,
        shot: Shot,
        scene: Scene,
        breakdown: Optional[CameraShotBreakdown],
        clip_label: str,
        clip_index: int,
    ) -> str:
        timestamp = ""
        if self.config.include_timestamps:
            timestamp = f"[{format_timestamp(shot.start_time)}-{format_timestamp(shot.end_time)}] "

        label = self._clean_clip_label(clip_label) or clip_label
        camera_summary = self._compose_camera_prompt(shot, breakdown)
        clip_tag = f"Clip {clip_index:02d}"
        if camera_summary:
            return f"{timestamp}Shot {shot.shot_index} {clip_tag}: {label} ({camera_summary})"
        return f"{timestamp}Shot {shot.shot_index} {clip_tag}: {label}"
    
    def _create_shot_description(
        self,
        shot: Shot,
        scene: Scene,
        breakdown: Optional[CameraShotBreakdown] = None,
    ) -> str:
        """Create a human-readable shot description with cinematography cues."""

        timestamp = ""
        if self.config.include_timestamps:
            timestamp = f"[{format_timestamp(shot.start_time)}-{format_timestamp(shot.end_time)}] "

        _ = scene  # Not currently needed but retained for extensibility

        core = f"Shot {shot.shot_index}: {shot.description}"
        if shot.action:
            core += f" - {shot.action}"

        cinematography_bits: list[str] = []
        if breakdown:
            if breakdown.camera_shot_type:
                cinematography_bits.append(breakdown.camera_shot_type)
            if breakdown.camera_angle:
                cinematography_bits.append(f"{breakdown.camera_angle} angle")
            if breakdown.camera_height:
                cinematography_bits.append(breakdown.camera_height)
            if breakdown.camera_distance:
                cinematography_bits.append(breakdown.camera_distance)
            movement_phrase = self._movement_phrase(breakdown.camera_motion)
            if movement_phrase:
                cinematography_bits.append(movement_phrase)
        else:
            shot_type_str = self._humanize_shot_type(shot.shot_type)
            if shot_type_str:
                cinematography_bits.append(shot_type_str)
            movement_phrase = self._movement_phrase(shot.camera_movement)
            if movement_phrase:
                cinematography_bits.append(movement_phrase)

        cinematography_bits = self._unique_parts(cinematography_bits)
        if cinematography_bits:
            core += f" ({', '.join(cinematography_bits)})"

        return f"{timestamp}{core}"
    
    def _generate_notes(self, scene: Scene, report: VideoReport) -> str:
        """Generate director's notes for a scene."""
        notes_parts = []
        
        if scene.mood:
            notes_parts.append(f"Mood: {scene.mood}")
        
        if scene.lighting:
            notes_parts.append(f"Lighting: {scene.lighting}")
        
        if scene.style:
            notes_parts.append(f"Style: {scene.style}")
        
        if scene.camera_breakdowns:
            guidance = [b.recreation_guidance for b in scene.camera_breakdowns if b.recreation_guidance]
            guidance = self._unique_parts([g for g in guidance if g])
            if guidance:
                notes_parts.append("Camera recreation: " + "; ".join(guidance))

            lighting_moods = []
            for breakdown in scene.camera_breakdowns:
                if breakdown.lighting_style and breakdown.lighting_style.mood:
                    lighting_moods.append(breakdown.lighting_style.mood)
            lighting_moods = self._unique_parts(lighting_moods)
            if lighting_moods:
                notes_parts.append("Lighting mood cues: " + ", ".join(lighting_moods))
        
        notes_parts = self._unique_parts(notes_parts)
        return ". ".join(notes_parts) if notes_parts else None
    
    @staticmethod
    def load_report(report_path: Path) -> VideoReport:
        """Load a VideoReport from disk."""
        return load_model(report_path, VideoReport)
