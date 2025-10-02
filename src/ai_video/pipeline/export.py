"""Export utilities for prompts and reports."""

from pathlib import Path
from typing import List, Optional
import json

from ..models import PromptBundle, VideoReport, PromptSpec
from ..paths import path_builder
from ..storage import write_text, write_json, load_model
from ..utils import format_timestamp
from ..logging import get_logger

logger = get_logger(__name__)

class PromptExporter:
    """Export prompt bundles to various formats."""
    
    @staticmethod
    def export_to_markdown(
        bundles: List[PromptBundle],
        output_path: Path,
        report: Optional[VideoReport] = None,
        include_metadata: bool = True
    ) -> None:
        """Export prompt bundles to Markdown format."""
        logger.info(f"Exporting prompts to Markdown: {output_path}")
        
        lines = []
        
        if include_metadata and report:
            lines.append(f"# Prompts for {report.title or report.video_id}\n")
            lines.append(f"**Source:** {report.source}\n")
            lines.append(f"**Duration:** {report.duration}s\n")
            if report.summary:
                lines.append(f"**Summary:** {report.summary}\n")
            lines.append("\n---\n")
        else:
            lines.append("# Video Prompts\n")
        
        for bundle in bundles:
            lines.append(f"\n## Scene {bundle.scene_index}")
            lines.append(f"**Time:** {format_timestamp(bundle.start_time)} - {format_timestamp(bundle.end_time)} ({bundle.duration:.1f}s)\n")
            
            if bundle.notes:
                lines.append(f"**Notes:** {bundle.notes}\n")
            
            if bundle.shot_descriptions:
                lines.append("\n### Shot List\n")
                for desc in bundle.shot_descriptions:
                    lines.append(f"- {desc}")
                lines.append("")
            
            if bundle.image_prompts:
                lines.append("\n### Image Generation Prompts (Text-to-Image)\n")
                for i, prompt in enumerate(bundle.image_prompts, 1):
                    lines.append(f"**Prompt {i}:**")
                    lines.append(f"```")
                    lines.append(prompt.text)
                    lines.append(f"```")
                    if prompt.negative_prompt:
                        lines.append(f"*Negative:* {prompt.negative_prompt}")
                    lines.append("")
            
            if bundle.video_prompts:
                lines.append("\n### Video Generation Prompts (Image-to-Video / Text-to-Video)\n")
                for i, prompt in enumerate(bundle.video_prompts, 1):
                    lines.append(f"**Prompt {i}:**")
                    lines.append(f"```")
                    lines.append(prompt.text)
                    lines.append(f"```")
                    lines.append("")
            
            lines.append("\n---\n")
        
        content = "\n".join(lines)
        write_text(content, output_path)
        logger.info(f"Markdown export completed: {output_path}")
    
    @staticmethod
    def export_to_json(
        bundles: List[PromptBundle],
        output_path: Path,
        report: Optional[VideoReport] = None,
        include_metadata: bool = True
    ) -> None:
        """Export prompt bundles to JSON format."""
        logger.info(f"Exporting prompts to JSON: {output_path}")
        
        data = {
            "metadata": {},
            "scenes": []
        }
        
        if include_metadata and report:
            data["metadata"] = {
                "video_id": report.video_id,
                "source": report.source,
                "duration": report.duration,
                "title": report.title,
                "summary": report.summary,
            }
        
        for bundle in bundles:
            scene_data = {
                "scene_index": bundle.scene_index,
                "start_time": bundle.start_time,
                "end_time": bundle.end_time,
                "duration": bundle.duration,
                "notes": bundle.notes,
                "shot_descriptions": bundle.shot_descriptions,
                "image_prompts": [p.model_dump() for p in bundle.image_prompts],
                "video_prompts": [p.model_dump() for p in bundle.video_prompts],
            }
            data["scenes"].append(scene_data)
        
        write_json(data, output_path)
        logger.info(f"JSON export completed: {output_path}")
    
    @staticmethod
    def export_shot_list(
        bundles: List[PromptBundle],
        output_path: Path,
        format: str = "simple"
    ) -> None:
        """Export a simple shot list."""
        logger.info(f"Exporting shot list: {output_path}")
        
        lines = ["# Shot List\n"]
        
        for bundle in bundles:
            lines.append(f"\n## Scene {bundle.scene_index} ({format_timestamp(bundle.start_time)} - {format_timestamp(bundle.end_time)})\n")
            
            for desc in bundle.shot_descriptions:
                lines.append(f"- {desc}")
            
            if not bundle.shot_descriptions:
                lines.append(f"- Scene duration: {bundle.duration:.1f}s")
            
            lines.append("")
        
        content = "\n".join(lines)
        write_text(content, output_path)
        logger.info(f"Shot list export completed: {output_path}")
    
    @staticmethod
    def load_bundles_from_video_id(video_id: str) -> List[PromptBundle]:
        """Load all prompt bundles for a video ID."""
        prompts_dir = path_builder.get_video_prompts_dir(video_id)
        
        bundles = []
        for bundle_file in sorted(prompts_dir.glob("scene_*.json")):
            bundle = load_model(bundle_file, PromptBundle)
            bundles.append(bundle)
        
        return bundles
    
    @staticmethod
    def export_all_formats(
        video_id: str,
        report: Optional[VideoReport] = None,
        output_dir: Optional[Path] = None
    ) -> dict:
        """Export prompts in all formats."""
        if output_dir is None:
            output_dir = path_builder.get_video_prompts_dir(video_id)
        
        bundles = PromptExporter.load_bundles_from_video_id(video_id)
        
        paths = {}
        
        json_path = output_dir / "prompts.json"
        PromptExporter.export_to_json(bundles, json_path, report, include_metadata=True)
        paths["json"] = str(json_path)
        
        shot_list_path = output_dir / "shot_list.md"
        PromptExporter.export_shot_list(bundles, shot_list_path)
        paths["shot_list"] = str(shot_list_path)
        
        logger.info(f"Exported all formats for video: {video_id}")
        return paths
