"""Reimagination agent for generating creative prompt variants per scene."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer
from google import genai
from google.genai import types
from pydantic import ValidationError as PydanticValidationError

from ..logging import get_logger, LogContext
from ..models import (
    GlobalStyleProfile,
    ReimaginedScene,
    ReimaginedVariant,
    ReimaginationResult,
)
from ..safety import ValidationError, validate_api_key
from ..settings import settings
from ..storage import read_text, write_json, write_text

logger = get_logger(__name__)

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "reimagination_agent_system_prompt.md"

PROMPT_STRUCTURE = "Subject + Action + Scene + Camera + Lighting + Style"

LIGHT_CONDITIONS = [
    "golden hour",
    "blue hour",
    "overcast light",
    "diffused light",
    "backlighting",
    "soft ambient light",
    "low-key lighting",
    "high-key lighting",
    "window light",
    "dappled light",
    "spotlight",
    "twilight light",
    "candlelight",
    "neon light",
    "moonlight",
    "street light",
    "bounced light",
    "lens flare",
    "studio light",
    "pattern light",
]

FILM_STOCK_CHOICES = [
    "Cinestill 800T",
    "Kodak Portra 800",
    "Lomography X-Pro 200",
    "Kodak Ektachrome",
    "Fujifilm Pro 400H",
    "Lomography Color Negative 800",
    "Kodak Ektar 100",
    "Revolog Kolor",
    "Agfa Vista Plus 200",
    "Fujifilm Velvia 50",
    "Fujifilm Superia X-Tra",
    "Kodak Gold 200",
    "Fujifilm Provia 100F",
    "Adox Color Implosion",
    "Agfa Vista 400",
    "Lomography Redscale",
    "Kodak Vision3 500T",
    "Lomography Diana F+",
    "Polaroid Originals",
    "Fujifilm Instax Mini",
]

@dataclass
class ParsedScene:
    """Intermediate representation of a scene extracted from markdown."""

    scene_index: int
    scene_title: str
    description: str = ""
    location: Optional[str] = None
    mood: Optional[str] = None
    lighting: Optional[str] = None
    original_style: Optional[str] = None
    base_prompt: Optional[str] = None
    prompt_source: Optional[str] = None
    time_range: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParsedDocument:
    """Parsed markdown document with scenes."""

    video_id: str
    title: Optional[str]
    film_stock: Optional[str]
    lens: Optional[str]
    base_style: Optional[str]
    base_mood: Optional[str]
    cultural_context: Optional[str]
    scenes: List[ParsedScene]


def parse_detailed_markdown(input_path: Path) -> ParsedDocument:
    """Parse the prompts_detailed markdown file and extract scene information."""
    text = read_text(input_path)
    lines = text.splitlines()

    scene_header = re.compile(r"^##\s+Scene\s+(\d+)(?::|\-|\u2013)?\s*(.*)?$", re.IGNORECASE)
    bold_field = re.compile(r"^\*\*(.+?):\*\*\s*(.*)$")

    document_title: Optional[str] = None
    video_id: Optional[str] = None
    film_stock: Optional[str] = None
    lens: Optional[str] = None
    base_style: Optional[str] = None
    base_mood: Optional[str] = None
    cultural_context: Optional[str] = None
    scenes: List[ParsedScene] = []
    current: Optional[ParsedScene] = None

    prompts_map = _load_prompt_map(input_path.parent)

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()

        if not document_title and line.startswith("# "):
            document_title = line.lstrip("# ").strip()
        elif not video_id and line.startswith("**Video ID:**"):
            video_id = line.split("**Video ID:**", 1)[1].strip()

        lower_line = line.lower()
        if lower_line.startswith("### film stock"):
            i += 1
            section_lines: List[str] = []
            while i < len(lines):
                section_line = lines[i].strip()
                if not section_line or section_line.startswith("###") or section_line.startswith("## "):
                    break
                section_lines.append(section_line)
                i += 1
            film_stock = " ".join(section_lines).strip() or film_stock
            continue
        if lower_line.startswith("### lens"):
            i += 1
            section_lines = []
            while i < len(lines):
                section_line = lines[i].strip()
                if not section_line or section_line.startswith("###") or section_line.startswith("## "):
                    break
                section_lines.append(section_line)
                i += 1
            lens = " ".join(section_lines).strip() or lens
            continue
        if lower_line.startswith("### style"):
            i += 1
            section_lines = []
            while i < len(lines):
                section_line = lines[i].strip()
                if not section_line or section_line.startswith("###") or section_line.startswith("## "):
                    break
                section_lines.append(section_line)
                i += 1
            base_style = " ".join(section_lines).strip() or base_style
            continue
        if lower_line.startswith("### mood"):
            i += 1
            section_lines = []
            while i < len(lines):
                section_line = lines[i].strip()
                if not section_line or section_line.startswith("###") or section_line.startswith("## "):
                    break
                section_lines.append(section_line)
                i += 1
            base_mood = " ".join(section_lines).strip() or base_mood
            continue
        if lower_line.startswith("### cultural context"):
            i += 1
            section_lines = []
            while i < len(lines):
                section_line = lines[i].strip()
                if not section_line or section_line.startswith("###") or section_line.startswith("## "):
                    break
                section_lines.append(section_line)
                i += 1
            cultural_context = " ".join(section_lines).strip() or cultural_context
            continue

        header_match = scene_header.match(line)
        if header_match:
            if current:
                scenes.append(current)
            index = int(header_match.group(1))
            title = header_match.group(2).strip() if header_match.group(2) else f"Scene {index}"
            current = ParsedScene(scene_index=index, scene_title=title)
            i += 1
            continue

        if current is None:
            i += 1
            continue

        field_match = bold_field.match(line)
        if field_match:
            label = field_match.group(1).lower()
            value = field_match.group(2).strip()

            if label.startswith("description"):
                description_lines: List[str] = []
                i += 1
                while i < len(lines) and lines[i].strip():
                    description_lines.append(lines[i].strip())
                    i += 1
                current.description = " ".join(description_lines).strip()
                continue
            if label.startswith("mood"):
                current.mood = value or None
            elif label.startswith("lighting"):
                current.lighting = value or None
            elif label.startswith("style") and not current.original_style:
                current.original_style = value or None
            elif "time" in label:
                current.time_range = value or None
            elif "location" in label and not current.location:
                current.location = value or None
            else:
                current.extras[label] = value

        if line.lower().startswith("#### text-to-image prompt"):
            code_lines: List[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                i += 1
            if i < len(lines) and lines[i].strip().startswith("```"):
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i].rstrip())
                    i += 1
                current.base_prompt = "\n".join(code_lines).strip()
                current.prompt_source = "markdown_text_to_image"
                if i < len(lines) and lines[i].strip().startswith("```"):
                    i += 1
                continue

        i += 1

    if current:
        scenes.append(current)

    for scene in scenes:
        if not scene.base_prompt:
            json_prompt = prompts_map.get(scene.scene_index)
            if json_prompt:
                scene.base_prompt = json_prompt
                scene.prompt_source = "prompts_json"

    resolved_video_id = video_id or input_path.parent.name

    return ParsedDocument(
        video_id=resolved_video_id,
        title=document_title,
        film_stock=film_stock,
        lens=lens,
        base_style=base_style,
        base_mood=base_mood,
        cultural_context=cultural_context,
        scenes=scenes,
    )


def _load_prompt_map(parent_dir: Path) -> Dict[int, str]:
    """Load prompt text from prompts.json or per-scene JSON files."""
    prompt_map: Dict[int, str] = {}

    prompts_json = parent_dir / "prompts.json"
    if prompts_json.exists():
        try:
            data = json.loads(read_text(prompts_json))
            for scene in data.get("scenes", []):
                scene_index = scene.get("scene_index")
                if not scene_index:
                    continue
                image_prompts = scene.get("image_prompts") or []
                if image_prompts:
                    text = image_prompts[0].get("text")
                    if text:
                        prompt_map.setdefault(scene_index, text.strip())
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to read prompts.json: %s", exc)

    if prompt_map:
        return prompt_map

    for json_file in sorted(parent_dir.glob("scene_*.json")):
        try:
            data = json.loads(read_text(json_file))
            scene_index = data.get("scene_index")
            image_prompts = data.get("image_prompts") or []
            if scene_index and image_prompts:
                text = image_prompts[0].get("text")
                if text:
                    prompt_map.setdefault(scene_index, text.strip())
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to read %s: %s", json_file, exc)

    return prompt_map

class ReimaginationAgent:
    """Agent responsible for generating reimagined variants for each scene."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[genai.Client] = None,
    ) -> None:
        self.api_key = api_key or settings.google_api_key
        validate_api_key(self.api_key)

        self.model = model or settings.gemini.model
        self.client = client or genai.Client(api_key=self.api_key)
        self.max_retries = settings.gemini.max_retries
        self.system_prompt = self._load_system_prompt()

    def generate_reimagined_prompts(
        self,
        input_file: str,
        style: Optional[str] = None,
        num_variants: int = 3,
        output_dir: Optional[str] = None,
        user_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate reimagined prompt variants for each scene in the markdown file."""
        input_path = Path(input_file)
        if not input_path.exists():
            raise ValidationError(f"Input file not found: {input_path}")
        if num_variants < 1 or num_variants > 5:
            raise ValidationError("num_variants must be between 1 and 5 inclusive")

        with LogContext(logger, f"Reimagining prompts from {input_path}"):
            parsed = parse_detailed_markdown(input_path)
            if not parsed.scenes:
                raise ValidationError("No scenes found in markdown document")

            global_style = self._determine_global_style(parsed, style)
            reimagined_scenes: List[ReimaginedScene] = []

            for scene in parsed.scenes:
                reimagined_scene = self.reimagine_scene(
                    scene=scene,
                    global_style=global_style,
                    num_variants=num_variants,
                    document=parsed,
                    user_prompt=user_prompt,
                )
                reimagined_scenes.append(reimagined_scene)

            result = ReimaginationResult(
                video_id=parsed.video_id,
                source_file=str(input_path),
                generated_at=datetime.utcnow(),
                requested_style=style,
                user_prompt=user_prompt,
                global_style=global_style,
                num_variants_per_scene=num_variants,
                total_scenes=len(reimagined_scenes),
                total_variants=sum(len(scene.reimagined_variants) for scene in reimagined_scenes),
                scenes=reimagined_scenes,
            )

            output_base = Path(output_dir) if output_dir else input_path.parent
            output_base.mkdir(parents=True, exist_ok=True)
            artifacts = self._write_outputs(result, output_base)
            result.artifacts = artifacts

            return result.model_dump(mode="json")

    def reimagine_scene(
        self,
        scene: ParsedScene,
        global_style: GlobalStyleProfile,
        num_variants: int,
        document: ParsedDocument,
        user_prompt: Optional[str],
    ) -> ReimaginedScene:
        """Generate reimagined variants for a single scene."""
        # Determine if we're in Creative Reimagination Mode
        is_creative_mode = bool(user_prompt)
        
        payload = {
            "mode": "creative_reimagination" if is_creative_mode else "standard",
            "global_style": global_style.model_dump(),
            "scene": {
                "scene_index": scene.scene_index,
                "scene_title": scene.scene_title,
                "location": scene.location,
                "description": scene.description,
                "mood": scene.mood,
                "lighting": scene.lighting,
                "original_style": scene.original_style,
                "base_prompt": scene.base_prompt,
                "time_range": scene.time_range,
            },
            "global_context": {
                "film_stock": document.film_stock,
                "lens": document.lens,
                "style": document.base_style,
                "mood": document.base_mood,
                "cultural_context": document.cultural_context,
            },
            "reference_guides": {
                "prompt_structure": PROMPT_STRUCTURE,
                "lighting_options": LIGHT_CONDITIONS,
                "film_stock_options": FILM_STOCK_CHOICES,
                "language_style": "Use clear, conversational sentences while keeping technical camera and lighting terms precise.",
            },
            "requirements": {
                "num_variants": num_variants,
                "creative_mode_enabled": is_creative_mode,
                "preserve_subject_action": not is_creative_mode,  # False in creative mode
                "prompt_guidelines": {
                    "min_word_count": 80,
                    "max_word_count": 130,
                    "include_film_stock": True,
                    "include_lens": True,
                    "include_mood": True,
                    "include_cultural_context": True,
                },
                "max_prompt_length": 350,
                "mandatory_fields": {
                    "film_stock": "REQUIRED - must be one from the provided list or a professional alternative; will be embedded in the prompt text",
                    "lens": "REQUIRED - must be specified (e.g., '35mm prime', 'anamorphic', 'wide-angle'); will be embedded in the prompt text",
                    "mood": "REQUIRED - emotional/aesthetic tone for this variant; must be woven into the prompt description",
                    "cultural_context": "REQUIRED - relevant cultural grounding; must appear in the prompt or as explicit metadata",
                },
            },
        }
        if user_prompt:
            payload["requirements"]["user_prompt"] = user_prompt
        
        if is_creative_mode:
            instructions = (
                "CREATIVE REIMAGINATION MODE: The user has provided a custom creative directive. "
                "This directive takes ABSOLUTE PRECEDENCE. You are not bound by the original scene's subject, action, location, or any details. "
                "Use the original prompts ONLY as inspiration or a creative blueprint—you may completely reimagine the scene. "
                "Generate brand new subject matter, locations, actions, and compositions that fulfill the user's vision. "
                "You have complete creative freedom.\n\n"
                "CRITICAL REQUIREMENT: Every prompt must weave in ALL of the following elements:\n"
                "  1. Film Stock: Name a specific film stock and describe its visual character\n"
                "  2. Lens Choice: Specify the lens (focal length, type, aperture) and its effect on framing\n"
                "  3. Mood: Embed the emotional/aesthetic tone throughout the prompt\n"
                "  4. Cultural Context: Weave in relevant cultural or geographical cues\n\n"
                "For every variant:\n"
                "- Create prompts that are entirely NEW and INDEPENDENT from the original source material\n"
                "- Channel the user's directive faithfully—let it drive every creative choice\n"
                "- Each variant should showcase a unique interpretation of the user's vision\n"
                "- Use approachable language while weaving in precise camera and film terminology\n"
                "- Name-drop at least one relevant filmmaker, photographer, or designer whose work matches the mood\n"
                "- Draw lighting terms from the provided light-condition list and film stocks from the color film roster\n"
                "- Reference cultural context when appropriate\n"
                "- Stay within 300 words per prompt using short, readable sentences\n\n"
                "Return BOTH `image_prompt` and `video_prompt` per variant using: Subject + Action + Scene + Camera + Lighting + Style.\n"
                "Describe the video prompt with explicit movement cues and pacing.\n"
                "JSON structure: {scene_index, scene_title, notes?, reimagined_variants: ["
                "{variant_id, title, image_prompt, video_prompt, film_stock, lens, mood, cultural_context, style_notes?, camera_focus?, lighting_focus?, tags[]}]}\n\n"
                "USER DIRECTIVE (HIGHEST PRIORITY): " + user_prompt.strip()
            )
        else:
            instructions = (
                "STANDARD MODE: Create clear, production-ready generation prompts that keep the original subject and action "
                "but explore new moods, palettes, and settings aligned with the global style. Use approachable "
                "language while weaving in precise camera and film terminology (shot type, lens, movement, lighting). "
                "Each variant must name-drop at least one relevant filmmaker, photographer, or designer whose work matches the mood. "
                "Draw lighting terms from the provided light-condition list and film stocks from the color film roster. "
                "Always reference the cultural context when appropriate. Preserve branded elements and original locations as specified. "
                "Stay within 300 words per prompt using short, readable sentences.\n\n"
                "CRITICAL REQUIREMENT: Every prompt must weave in ALL of the following elements:\n"
                "  1. Film Stock: Name a specific film stock and describe its visual character (e.g., warm grain, color saturation)\n"
                "  2. Lens Choice: Specify the lens (focal length, type, aperture) and describe its framing effect\n"
                "  3. Mood: Embed the emotional/aesthetic tone throughout the prompt (not just as a tag)\n"
                "  4. Cultural Context: Weave in relevant cultural or geographical cues\n\n"
                "For every variant return BOTH an `image_prompt` and a `video_prompt`: structure them using the formula "
                "Subject + Action + Scene + Camera + Lighting + Style, inspired by the how-to-prompt guide. Describe the video prompt with explicit movement cues and pacing. "
                "The JSON structure MUST be: {scene_index, scene_title, notes?, reimagined_variants: ["
                "{variant_id, title, image_prompt, video_prompt, film_stock, lens, mood, cultural_context, style_notes?, camera_focus?, lighting_focus?, tags[]}]}"
            )


        response = self._invoke_model(instructions, payload)

        try:
            reimagined_scene = ReimaginedScene(**response)
        except PydanticValidationError as exc:
            logger.error("Invalid scene response: %s", exc)
            raise ValidationError("Model returned malformed scene data") from exc

        merged_scene = reimagined_scene.model_copy(
            update={
                "scene_index": scene.scene_index,
                "scene_title": reimagined_scene.scene_title or scene.scene_title,
                "location": reimagined_scene.location or scene.location,
                "original_description": reimagined_scene.original_description or scene.description,
                "original_prompt": reimagined_scene.original_prompt or scene.base_prompt,
                "mood": reimagined_scene.mood or scene.mood,
            }
        )

        updated_variants: List[ReimaginedVariant] = []
        for idx, variant in enumerate(merged_scene.reimagined_variants, start=1):
            update_data: Dict[str, Any] = {}
            if not variant.variant_id:
                update_data["variant_id"] = f"{scene.scene_index}-{idx:02d}"
            if not variant.image_prompt and variant.prompt:
                update_data["image_prompt"] = variant.prompt
            if not variant.video_prompt and variant.prompt:
                update_data["video_prompt"] = variant.prompt
            # MANDATORY: Always ensure these fields are populated
            if not variant.film_stock:
                if document.film_stock:
                    update_data["film_stock"] = document.film_stock
                else:
                    # Fallback: extract from prompt or use a reasonable default
                    update_data["film_stock"] = "Kodak Portra 800"
            if not variant.lens:
                if document.lens:
                    update_data["lens"] = document.lens
                else:
                    update_data["lens"] = "35mm prime lens"
            if not variant.mood:
                mood_val = scene.mood or document.base_mood or "cinematic"
                update_data["mood"] = mood_val
            if not variant.cultural_context:
                if document.cultural_context:
                    update_data["cultural_context"] = document.cultural_context
                else:
                    update_data["cultural_context"] = "Contemporary global context"
            updated_variants.append(variant.model_copy(update=update_data))

        return merged_scene.model_copy(update={"reimagined_variants": updated_variants})

    def choose_self_directed_style(self, parsed: ParsedDocument) -> GlobalStyleProfile:
        """Select a global creative direction when none is provided."""
        payload = {
            "video_id": parsed.video_id,
            "title": parsed.title,
            "global_context": {
                "film_stock": parsed.film_stock,
                "lens": parsed.lens,
                "style": parsed.base_style,
                "mood": parsed.base_mood,
                "cultural_context": parsed.cultural_context,
            },
            "reference_guides": {
                "prompt_structure": PROMPT_STRUCTURE,
                "lighting_options": LIGHT_CONDITIONS,
                "film_stock_options": FILM_STOCK_CHOICES,
            },
            "scenes": [
                {
                    "scene_index": scene.scene_index,
                    "location": scene.location,
                    "description": scene.description,
                    "mood": scene.mood,
                    "lighting": scene.lighting,
                    "current_style": scene.original_style,
                }
                for scene in parsed.scenes[:8]  # first 8 scenes give enough context
            ],
        }
        instructions = (
            "Analyze the provided scenes and propose a single cohesive creative direction that "
            "could be applied across all scenes. Respect the supplied film stock, lens, and "
            "cultural context when crafting the direction. Return JSON with fields: name, "
            "description, keywords (array of 3-6 tokens), palette, lighting, camera_direction."
        )
        response = self._invoke_model(instructions, payload)

        try:
            return GlobalStyleProfile(**response)
        except PydanticValidationError as exc:
            logger.error("Invalid style profile: %s", exc)
            raise ValidationError("Model returned malformed style profile") from exc

    def _determine_global_style(
        self,
        parsed: ParsedDocument,
        style_directive: Optional[str],
    ) -> GlobalStyleProfile:
        if style_directive:
            keywords = [token.strip() for token in re.split(r"[,:/]", style_directive) if token.strip()]
            description_parts = [f"User-provided directive emphasizing {style_directive.strip()}"]
            if parsed.film_stock:
                description_parts.append(f"Maintain film stock character: {parsed.film_stock}")
            if parsed.lens:
                description_parts.append(f"Lens reference: {parsed.lens}")
            if parsed.cultural_context:
                description_parts.append(f"Cultural context: {parsed.cultural_context}")
            return GlobalStyleProfile(
                name=style_directive.strip(),
                description=" | ".join(description_parts),
                keywords=keywords[:6],
                palette=None,
                lighting=None,
                camera_direction=None,
            )
        return self.choose_self_directed_style(parsed)

    def _invoke_model(self, instructions: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the Gemini model and parse the JSON response."""
        prompt = self._compose_prompt(instructions, payload)
        raw_response = self._call_model(prompt)
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode model response as JSON: %s", raw_response)
            raise ValidationError("Model response was not valid JSON") from exc

    def _call_model(self, prompt: str) -> str:
        """Call the Gemini model with retries."""
        config = types.GenerateContentConfig(response_mime_type="application/json")
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                content = types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)],
                )
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[content],
                    config=config,
                )
                return self._extract_text(response)
            except Exception as exc:  # pragma: no cover - network errors
                last_error = exc
                logger.warning("Model call failed (attempt %s/%s): %s", attempt, self.max_retries, exc)
        raise ValidationError(f"Failed to generate content after {self.max_retries} attempts") from last_error

    def _extract_text(self, response: Any) -> str:
        """Extract text content from Gemini response."""
        if hasattr(response, "text") and response.text:
            return response.text
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) if content else None
            if not parts:
                continue
            for part in parts:
                text = getattr(part, "text", None)
                if text:
                    return text
        raise ValidationError("Model returned empty response")

    def _compose_prompt(self, instructions: str, payload: Dict[str, Any]) -> str:
        serialized_payload = json.dumps(payload, indent=2, ensure_ascii=False)
        return (
            f"{self.system_prompt}\n\n"
            "-----\n"
            f"{instructions.strip()}\n\n"
            "Respond with STRICT JSON only. Do not include Markdown fences or commentary.\n"
            "Input payload:\n"
            f"{serialized_payload}\n"
        )

    def _write_outputs(self, result: ReimaginationResult, output_dir: Path) -> Dict[str, str]:
        json_path = output_dir / "variant_prompts.json"
        md_path = output_dir / "variant_report.md"

        write_json(result, json_path)
        write_text(render_markdown_report(result), md_path)

        return {"json": str(json_path), "markdown": str(md_path)}

    def _load_system_prompt(self) -> str:
        if not SYSTEM_PROMPT_PATH.exists():
            raise ValidationError(f"System prompt file not found: {SYSTEM_PROMPT_PATH}")
        return read_text(SYSTEM_PROMPT_PATH).strip()


def render_markdown_report(result: ReimaginationResult) -> str:
    """Render a concise markdown report summarizing generated variants."""
    header_title = result.global_style.name or "Reimagined Variants"
    lines = [
        f"# Reimagined Prompt Variants — {result.video_id}",
        "",
        f"**Generated:** {result.generated_at.isoformat()}",
        f"**Scenes Processed:** {result.total_scenes}",
        f"**Variants per Scene:** {result.num_variants_per_scene}",
        f"**Total Variants:** {result.total_variants}",
        "",
        "---",
        "",
        "## Global Style",
        f"**Name:** {header_title}",
    ]
    if result.user_prompt:
        lines.insert(6, f"**User Prompt:** {result.user_prompt}")

    if result.global_style.description:
        lines.append(f"**Description:** {result.global_style.description}")
    if result.global_style.keywords:
        keywords = ", ".join(result.global_style.keywords)
        lines.append(f"**Keywords:** {keywords}")
    if result.global_style.palette:
        lines.append(f"**Palette:** {result.global_style.palette}")
    if result.global_style.lighting:
        lines.append(f"**Lighting:** {result.global_style.lighting}")
    if result.global_style.camera_direction:
        lines.append(f"**Camera Direction:** {result.global_style.camera_direction}")

    lines.extend(["", "---", "", "## Scenes"])

    for scene in result.scenes:
        title_line = f"### Scene {scene.scene_index}: {scene.scene_title}" if scene.scene_title else f"### Scene {scene.scene_index}"
        lines.extend([title_line, ""])

        if scene.location:
            lines.append(f"- **Location:** {scene.location}")
        if scene.mood:
            lines.append(f"- **Original Mood:** {scene.mood}")
        if scene.original_description:
            lines.append(f"- **Original Description:** {scene.original_description}")

        lines.append("- **Variants:**")
        for variant in scene.reimagined_variants:
            tag_str = f" (tags: {', '.join(variant.tags)})" if variant.tags else ""
            lines.append(f"  - **{variant.title}**{tag_str}")
            if variant.image_prompt:
                lines.append("    ```")
                lines.append(f"    Image prompt: {variant.image_prompt}")
                lines.append("    ```")
            if variant.video_prompt:
                lines.append("    ```")
                lines.append(f"    Video prompt: {variant.video_prompt}")
                lines.append("    ```")
            if variant.film_stock:
                lines.append(f"    *Film stock:* {variant.film_stock}")
            if variant.lens:
                lines.append(f"    *Lens:* {variant.lens}")
            if variant.mood:
                lines.append(f"    *Mood:* {variant.mood}")
            if variant.cultural_context:
                lines.append(f"    *Cultural context:* {variant.cultural_context}")
            if variant.style_notes:
                lines.append(f"    *Style notes:* {variant.style_notes}")
            if variant.camera_focus:
                lines.append(f"    *Camera:* {variant.camera_focus}")
            if variant.lighting_focus:
                lines.append(f"    *Lighting:* {variant.lighting_focus}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"

app = typer.Typer(add_completion=False, help="Standalone CLI for the ReimaginationAgent")

@app.command()
def main(
    input: str = typer.Option(..., "--input", "-i", help="Path to prompts_detailed.md"),
    style: Optional[str] = typer.Option(None, "--style", "-s", help="Global style directive"),
    num_variants: int = typer.Option(3, "--num-variants", "-n", help="Number of variants per scene (1-5)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Override output directory"),
    model: Optional[str] = typer.Option(None, "--model", help="Override Gemini model"),
    user_prompt: Optional[str] = typer.Option(
        None,
        "--user-prompt",
        "-u",
        help="Additional free-form instructions applied to every variant",
    ),
) -> None:
    """Generate reimagined prompts directly from the CLI."""
    try:
        agent = ReimaginationAgent(model=model)
        result = agent.generate_reimagined_prompts(
            input_file=input,
            style=style,
            num_variants=num_variants,
            output_dir=output,
            user_prompt=user_prompt,
        )
        artifacts = result.get("artifacts", {})
        typer.echo(
            f"Generated {result['total_variants']} variants across {result['total_scenes']} scenes."
        )
        if artifacts:
            typer.echo(f"JSON output: {artifacts.get('json')}")
            typer.echo(f"Markdown report: {artifacts.get('markdown')}")
    except ValidationError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)

# Convenience for `python -m ai_video.agents.reimagination_agent`
if __name__ == "__main__":
    app()
