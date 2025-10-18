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

SHOT_FRAMING_GUIDE = {
    "Extreme close-up": "extreme close-up framing",
    "Close-up": "close-up framing",
    "Medium close-up": "medium close-up framing",
    "Medium shot": "medium shot framing",
    "Full body shot": "full body shot framing",
    "Wide shot": "wide shot framing",
    "Long shot": "long shot framing",
    "Wide establishing shot": "wide shot framing",
    "Two-shot": "two-shot framing",
    "Over-the-shoulder shot": "over-the-shoulder framing",
    "Point-of-view shot": "point-of-view framing",
}


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

    def _infer_camera_angle(self, shot: Shot) -> str:
        text_sources = " ".join(filter(None, [shot.camera_angle_degrees, shot.camera_description]))
        text = text_sources.lower()

        angle_value = self._extract_number(shot.camera_angle_degrees)
        if angle_value is not None:
            if angle_value >= 60:
                return "bird's-eye view"
            if angle_value <= -60:
                return "worm's-eye view"
            if angle_value >= 25:
                return "high-angle"
            if angle_value <= -25:
                return "low-angle"
            if angle_value > 10:
                return "gentle high-angle"
            if angle_value < -10:
                return "gentle low-angle"

        if any(keyword in text for keyword in ["bird", "aerial", "top-down", "overhead panorama"]):
            return "bird's-eye view"
        if any(keyword in text for keyword in ["worm", "ground", "from the floor"]):
            return "worm's-eye view"
        if any(keyword in text for keyword in ["overhead", "top", "downward", "high angle"]):
            return "high-angle"
        if any(keyword in text for keyword in ["low", "upward", "under"]):
            return "low-angle"
        if "dutch" in text or "canted" in text:
            return "dutch angle"
        if "tilt" in (shot.camera_movement or ""):
            if "up" in (shot.camera_movement or ""):
                return "low-angle"
            if "down" in (shot.camera_movement or ""):
                return "high-angle"
        return "eye-level"

    def _infer_camera_height(self, shot: Shot) -> str:
        height_value = self._extract_number(shot.camera_height_meters)

        if height_value is not None:
            if height_value < 1.0:
                return "ground-level camera placement"
            if height_value < 1.3:
                return "waist-level camera placement"
            if height_value < 1.5:
                return "chest-level camera placement"
            if height_value < 1.75:
                return "eye-level camera placement"
            if height_value < 2.2:
                return "slightly overhead camera placement"
            return "overhead camera placement"

        text = (shot.camera_position or "").lower()
        if "overhead" in text or "ceiling" in text:
            return "overhead camera placement"
        if "low" in text or "floor" in text or "ground" in text:
            return "ground-level camera placement"
        if "chest" in text:
            return "chest-level camera placement"
        if "waist" in text:
            return "waist-level camera placement"
        if "eye" in text:
            return "eye-level camera placement"
        return "eye-level camera placement"

    def _infer_camera_distance(self, shot: Shot) -> str:
        dist_value = self._extract_number(shot.camera_distance_meters)
        candidates: list[str] = []

        if dist_value is not None:
            if dist_value <= 0.7:
                candidates.append("extreme close-up framing")
            elif dist_value <= 1.6:
                candidates.append("close-up framing")
            elif dist_value <= 3.2:
                candidates.append("medium shot framing")
            elif dist_value <= 4.8:
                candidates.append("full body shot framing")
            elif dist_value <= 7.5:
                candidates.append("wide shot framing")
            else:
                candidates.append("long shot framing")

        description = (shot.description or "").lower()
        if "extreme" in description or "macro" in description:
            candidates.append("extreme close-up framing")
        if "close" in description or "intimate" in description:
            candidates.append("close-up framing")
        if any(term in description for term in ["medium", "waist", "portrait"]):
            candidates.append("medium shot framing")
        if "full" in description or "head-to-toe" in description:
            candidates.append("full body shot framing")
        if any(term in description for term in ["wide", "establishing", "panoramic", "sweeping"]):
            candidates.append("wide shot framing")
        if "distant" in description or "expansive" in description:
            candidates.append("long shot framing")

        shot_type_label = self._format_shot_type(shot.shot_type) if shot.shot_type else None
        if shot_type_label and shot_type_label in SHOT_FRAMING_GUIDE:
            candidates.append(SHOT_FRAMING_GUIDE[shot_type_label])

        for candidate in candidates:
            if candidate:
                return candidate

        return "medium shot framing"

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
                return "wide-angle lens"
            if focal_length <= 55:
                return "standard lens"
            if focal_length >= 70:
                return "telephoto lens"
            return "standard lens"

        lens_text = (shot.lens_focal_length or "").lower()
        if "wide" in lens_text:
            return "wide-angle lens"
        if "tele" in lens_text or "zoom" in lens_text:
            return "telephoto lens"
        if "anamorphic" in lens_text:
            return "anamorphic lens"
        numeric_estimate = self._extract_number(lens_text)
        if numeric_estimate is not None:
            if numeric_estimate <= 28:
                return "wide-angle lens"
            if numeric_estimate <= 55:
                return "standard lens"
            if numeric_estimate >= 70:
                return "telephoto lens"
            return "standard lens"
        if lens_text:
            return lens_text.strip()
        return None

    def _infer_depth_of_field(self, shot: Shot) -> Optional[str]:
        dof_text = (shot.depth_of_field or "").lower()
        if "shallow" in dof_text:
            return "shallow depth of field"
        if "deep" in dof_text:
            return "deep focus"
        if "medium" in dof_text:
            return "balanced depth of field"
        if dof_text:
            return dof_text

        if shot.shot_type:
            st = shot.shot_type.lower()
            if "close" in st:
                return "shallow depth of field"
            if "wide" in st or "establishing" in st:
                return "deep focus"
        return "balanced depth of field"

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
            short_height = camera_height.replace("camera ", "")
            guidance_parts.append(f"Keep the camera at {short_height}")
        if camera_distance:
            guidance_parts.append(f"Maintain {camera_distance}")
        if lens_type:
            guidance_parts.append(f"Pair with a {lens_type}")
        if framing_style:
            guidance_parts.append(f"Embrace a {framing_style.lower()} composition")

        key_light = lighting_style.key_light
        fill_light = lighting_style.fill_light
        practicals = lighting_style.practical_lights

        lighting_notes = []
        if key_light:
            lighting_notes.append(f"key light: {key_light}")
        if fill_light:
            lighting_notes.append(f"fill: {fill_light}")
        if practicals:
            lighting_notes.append(f"practicals: {practicals}")
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
