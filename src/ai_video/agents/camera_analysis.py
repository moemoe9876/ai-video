"""Cinematography-focused analysis helpers for enriching scene data."""

from __future__ import annotations

import re
from typing import Iterable, Optional, Sequence

from ..models import (
    CameraShotBreakdown,
    LightingStyleBreakdown,
    Scene,
    Shot,
    VideoReport,
)


class CameraVisionAnalyzer:
    """Translate analyzed scenes into cinematography-aware breakdowns."""

    def analyze_scene(self, scene: Scene, report: VideoReport) -> list[CameraShotBreakdown]:
        """Produce structured camera breakdowns for all shots in a scene."""

        if scene.shots:
            return [self._analyze_shot(scene, shot, report) for shot in scene.shots]
        # No shots: return no breakdowns to avoid speculative analysis
        return []

    # ------------------------------------------------------------------
    # Core builders
    # ------------------------------------------------------------------
    def _analyze_shot(self, scene: Scene, shot: Shot, report: VideoReport) -> CameraShotBreakdown:
        shot_type = self._format_shot_type(shot.shot_type)
        camera_angle = self._infer_camera_angle(shot)
        camera_height = self._infer_camera_height(shot)
        camera_distance = self._infer_camera_distance(shot)
        framing_style = self._infer_framing_style(shot)
        lens_type = self._infer_lens_type(shot)
        depth_of_field = self._infer_depth_of_field(shot)
        lighting_style = self._build_lighting_style(scene, report)
        composition_notes = self._build_composition_notes(scene, shot)
        set_design_notes = self._build_set_design_notes(scene)
        camera_motion = self._infer_camera_motion(shot)
        cinematic_purpose = self._infer_cinematic_purpose(scene, shot)
        recreation_guidance = self._build_recreation_guidance(
            camera_height,
            camera_distance,
            lens_type,
            lighting_style,
            framing_style,
            camera_motion,
        )

        scene_id = f"{scene.scene_index:03d}-{shot.shot_index:02d}"

        return CameraShotBreakdown(
            scene_id=scene_id,
            camera_shot_type=shot_type,
            camera_angle=camera_angle,
            camera_height=camera_height,
            camera_distance=camera_distance,
            framing_style=framing_style,
            lens_type_estimate=lens_type,
            depth_of_field=depth_of_field,
            lighting_style=lighting_style,
            composition_notes=composition_notes,
            set_design_notes=set_design_notes,
            camera_motion=camera_motion,
            cinematic_purpose=cinematic_purpose,
            recreation_guidance=recreation_guidance,
        )

    # ------------------------------------------------------------------
    # Inference helpers
    # ------------------------------------------------------------------
    def _format_shot_type(self, shot_type: Optional[str]) -> Optional[str]:
        if not shot_type:
            return None
        return shot_type.replace("_", " ").title()

    def _infer_camera_angle(self, shot: Shot) -> str:
        text_sources = " ".join(filter(None, [shot.camera_angle_degrees, shot.camera_description]))
        text = text_sources.lower()

        angle_value = self._extract_number(shot.camera_angle_degrees)
        if angle_value is not None:
            if angle_value >= 25:
                return "High"
            if angle_value <= -25:
                return "Low"
            if angle_value > 10:
                return "Slightly High"
            if angle_value < -10:
                return "Slightly Low"

        if any(keyword in text for keyword in ["overhead", "bird", "top", "downward", "high angle"]):
            return "High"
        if any(keyword in text for keyword in ["low", "worm", "upward", "under"]):
            return "Low"
        if "dutch" in text or "canted" in text:
            return "Dutch"
        if "tilt" in (shot.camera_movement or ""):
            if "up" in (shot.camera_movement or ""):
                return "Low"
            if "down" in (shot.camera_movement or ""):
                return "High"
        return "Eye-Level"

    def _infer_camera_height(self, shot: Shot) -> str:
        height_value = self._extract_number(shot.camera_height_meters)

        if height_value is not None:
            if height_value < 1.0:
                return f"Below waist (~{height_value:.1f}m)"
            if height_value < 1.3:
                return f"Waist-level (~{height_value:.1f}m)"
            if height_value < 1.5:
                return f"Chest-level (~{height_value:.1f}m)"
            if height_value < 1.75:
                return f"Eye-level (~{height_value:.1f}m)"
            if height_value < 2.2:
                return f"Slightly overhead (~{height_value:.1f}m)"
            return f"Overhead (~{height_value:.1f}m)"

        text = (shot.camera_position or "").lower()
        if "overhead" in text or "ceiling" in text:
            return "Overhead"
        if "low" in text or "floor" in text:
            return "Below waist"
        if "chest" in text:
            return "Chest-level"
        if "eye" in text:
            return "Eye-level"
        return "Eye-level"

    def _infer_camera_distance(self, shot: Shot) -> str:
        dist_value = self._extract_number(shot.camera_distance_meters)

        if dist_value is not None:
            if dist_value < 1.2:
                return f"Close (~{dist_value:.1f}m)"
            if dist_value < 2.5:
                return f"Medium (~{dist_value:.1f}m)"
            if dist_value < 5.0:
                return f"Far (~{dist_value:.1f}m)"
            return f"Long (~{dist_value:.1f}m)"

        description = (shot.description or "").lower()
        if "close" in description:
            return "Close"
        if "wide" in description or "establishing" in description:
            return "Long"
        return "Medium"

    def _infer_framing_style(self, shot: Shot) -> Optional[str]:
        position_text = (shot.subject_position_frame or "").lower()
        if not position_text:
            position_text = (shot.camera_description or "").lower()

        if "center" in position_text:
            return "Centered"
        if "symmetr" in position_text:
            return "Symmetrical"
        if "third" in position_text:
            return "Rule of Thirds"
        if "leading" in position_text or "diagonal" in position_text:
            return "Leading Lines"
        if position_text:
            return "Dynamic"
        return None

    def _infer_lens_type(self, shot: Shot) -> Optional[str]:
        focal_length = self._extract_number(shot.lens_focal_length)

        if focal_length is not None:
            if focal_length <= 28:
                return "Wide (≤28mm)"
            if focal_length <= 55:
                return "Normal (35–50mm)"
            if focal_length >= 70:
                return "Telephoto (70mm+)"
            return f"Normal (~{focal_length:.0f}mm)"

        lens_text = (shot.lens_focal_length or "").lower()
        if "wide" in lens_text:
            return "Wide (≤28mm)"
        if "tele" in lens_text or "zoom" in lens_text:
            return "Telephoto (70mm+)"
        if lens_text:
            return lens_text.title()
        return None

    def _infer_depth_of_field(self, shot: Shot) -> Optional[str]:
        dof_text = (shot.depth_of_field or "").lower()
        if "shallow" in dof_text:
            return "Shallow"
        if "deep" in dof_text:
            return "Deep"
        if "medium" in dof_text:
            return "Medium"
        if dof_text:
            return dof_text.title()

        if shot.shot_type:
            st = shot.shot_type.lower()
            if "close" in st:
                return "Shallow"
            if "wide" in st or "establishing" in st:
                return "Deep"
        return "Medium"

    def _build_lighting_style(self, scene: Scene, report: VideoReport) -> LightingStyleBreakdown:
        lighting_sources: list[str] = []
        for candidate in [scene.lighting, scene.lighting_type, scene.lighting_direction, scene.lighting_temperature]:
            if candidate:
                lighting_sources.append(str(candidate))
        consolidated = " ".join(lighting_sources)

        key_light = self._extract_sentence(consolidated, ["key light", "key"], fallback=scene.lighting_type)
        fill_light = self._extract_sentence(consolidated, ["fill"], fallback=scene.lighting_direction)
        practicals = self._extract_sentence(consolidated, ["practical", "bulb", "lamp", "neon", "window"])

        if not practicals:
            practicals = self._derive_practicals_from_environment(scene)

        mood = scene.mood or report.overall_mood or "Cinematic"

        return LightingStyleBreakdown(
            key_light=self._clean_text(key_light),
            fill_light=self._clean_text(fill_light),
            practical_lights=self._clean_text(practicals),
            mood=self._clean_text(mood),
        )

    def _build_composition_notes(self, scene: Scene, shot: Shot) -> Optional[str]:
        candidates = [shot.spatial_relationships, shot.camera_description, scene.description]
        for text in candidates:
            if text:
                cleaned = self._clean_text(text)
                if cleaned:
                    return cleaned
        return None

    def _build_set_design_notes(self, scene: Scene) -> Optional[str]:
        if not scene.physical_world:
            return None

        pw = scene.physical_world

        if isinstance(pw, str):
            return self._clean_text(pw)

        if isinstance(pw, dict):
            parts = []
            for key, value in pw.items():
                if not value:
                    continue
                label = key.replace("_", " ").title()
                if isinstance(value, (list, tuple)):
                    rendered = ", ".join(self._stringify_sequence(value))
                elif isinstance(value, dict):
                    rendered = ", ".join(self._stringify_sequence(value.values()))
                else:
                    rendered = str(value)
                if rendered:
                    parts.append(f"{label}: {rendered}")
            return "; ".join(parts) if parts else None

        return None

    def _infer_camera_motion(self, shot: Shot) -> str:
        movement = shot.camera_movement or "static"
        return movement.replace("_", " ").title()

    def _infer_cinematic_purpose(self, scene: Scene, shot: Shot) -> Optional[str]:
        elements = []
        if shot.action:
            elements.append(f"Highlights {shot.action.lower()}")
        if scene.mood:
            elements.append(f"reinforces {scene.mood.lower()}")
        if not elements and scene.description:
            elements.append(f"Supports {scene.description.lower()[:60]}...")
        return self._join_phrases(elements)

    def _build_recreation_guidance(
        self,
        camera_height: Optional[str],
        camera_distance: Optional[str],
        lens_type: Optional[str],
        lighting_style: LightingStyleBreakdown,
        framing_style: Optional[str],
        camera_motion: Optional[str],
    ) -> Optional[str]:
        guidance_parts: list[str] = []

        if camera_height:
            guidance_parts.append(f"Set camera height to {camera_height.lower()}")
        if camera_distance:
            guidance_parts.append(f"Keep camera {camera_distance.lower()} from subject")
        if lens_type:
            guidance_parts.append(f"Use {lens_type.lower()} optics")
        if framing_style:
            guidance_parts.append(f"Frame using a {framing_style.lower()} composition")

        key_light = lighting_style.key_light
        fill_light = lighting_style.fill_light
        practicals = lighting_style.practical_lights

        lighting_notes = []
        if key_light:
            lighting_notes.append(f"key light: {key_light.lower()}")
        if fill_light:
            lighting_notes.append(f"fill: {fill_light.lower()}")
        if practicals:
            lighting_notes.append(f"practicals: {practicals.lower()}")
        if lighting_notes:
            guidance_parts.append("Lighting setup with " + "; ".join(lighting_notes))

        if camera_motion and camera_motion.lower() != "static":
            guidance_parts.append(f"Execute a {camera_motion.lower()} move")

        return self._join_phrases(guidance_parts)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _extract_number(self, text: Optional[str]) -> Optional[float]:
        if not text:
            return None
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    def _extract_sentence(self, text: str, keywords: Sequence[str], fallback: Optional[str] = None) -> Optional[str]:
        if not text:
            return fallback
        sentences = re.split(r"(?<=[.!?])\s+", text)
        lowercase_keywords = [kw.lower() for kw in keywords]
        for sentence in sentences:
            lower_sentence = sentence.lower()
            if any(keyword in lower_sentence for keyword in lowercase_keywords):
                return sentence.strip()
        return fallback

    def _extract_from_text(self, text: Optional[str], keywords: Sequence[str]) -> Optional[str]:
        if not text:
            return None
        lower_text = text.lower()
        for keyword in keywords:
            if keyword.lower() in lower_text:
                return text
        return None

    def _derive_practicals_from_environment(self, scene: Scene) -> Optional[str]:
        physical_world = scene.physical_world
        if isinstance(physical_world, dict):
            for key, value in physical_world.items():
                if not value:
                    continue
                if isinstance(value, (list, tuple)):
                    joined = ", ".join(self._stringify_sequence(value))
                elif isinstance(value, dict):
                    joined = ", ".join(self._stringify_sequence(value.values()))
                else:
                    joined = str(value)
                if any(token in key.lower() for token in ["light", "lamp", "bulb", "neon"]):
                    return joined
                if "light" in joined.lower():
                    return joined
        return None

    def _stringify_sequence(self, values: Iterable[object]) -> list[str]:
        rendered: list[str] = []
        for value in values:
            if not value:
                continue
            if isinstance(value, dict):
                rendered.append(", ".join(self._stringify_sequence(value.values())))
            else:
                rendered.append(str(value))
        return [item for item in (val.strip() for val in rendered) if item]

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        cleaned = re.sub(r"\s+", " ", str(text)).strip()
        return cleaned or None

    def _join_phrases(self, phrases: Sequence[str]) -> Optional[str]:
        phrases = [self._clean_text(p) for p in phrases if p]
        phrases = [p for p in phrases if p]
        if not phrases:
            return None
        return "; ".join(phrases)

