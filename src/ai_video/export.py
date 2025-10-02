"""Export utilities for generating consolidated prompt files."""

from pathlib import Path
from typing import Optional
from datetime import datetime

from .models import VideoReport, Scene, Shot
from .logging import get_logger

logger = get_logger(__name__)


def generate_detailed_markdown(report: VideoReport, output_path: Path) -> None:
    """
    Generate ultra-detailed consolidated markdown file with all scene information.
    
    Args:
        report: VideoReport containing all analysis data
        output_path: Path where markdown file should be saved
    """
    video_id = report.video_id
    
    # Start markdown output
    md_lines = [
        f"# Ultra-Detailed Video Prompts: {report.title or video_id}",
        "",
        f"**Video ID:** {video_id}",
        f"**Duration:** {report.duration}s | **Total Scenes:** {len(report.scenes)}",
        "",
        "---",
        "",
        "## 🎬 Film Technical Specifications",
        "",
    ]
    
    # Film stock
    if report.film_stock_look:
        md_lines.extend([
            "### Film Stock",
            report.film_stock_look,
            ""
        ])
    
    # Lens
    if report.lens_characteristics:
        md_lines.extend([
            "### Lens",
            report.lens_characteristics,
            ""
        ])
    
    # Style
    if report.overall_style:
        md_lines.extend([
            "### Style",
            report.overall_style,
            ""
        ])
    
    # Mood
    if report.overall_mood:
        md_lines.extend([
            "### Mood",
            report.overall_mood,
            ""
        ])
    
    # Cultural context
    if report.cultural_context:
        md_lines.extend([
            "### Cultural Context",
            report.cultural_context,
            ""
        ])
    
    md_lines.extend(["---", ""])
    
    # Process each scene
    for scene_idx, scene in enumerate(report.scenes, 1):
        md_lines.extend([
            f"## Scene {scene_idx}",
            "",
            f"**⏱ Time:** {scene.start_time:.1f}s - {scene.end_time:.1f}s ({scene.duration:.1f}s)",
            f"**📍 Location:** {scene.location}",
            ""
        ])
        
        # Scene description
        if scene.description:
            md_lines.extend([
                "**Description:**",
                scene.description,
                ""
            ])
        
        # Mood and lighting
        if scene.mood:
            md_lines.append(f"**Mood:** {scene.mood}")
        if scene.lighting:
            md_lines.append(f"**Lighting:** {scene.lighting}")
        
        # Additional scene details
        if scene.time_of_day:
            md_lines.append(f"**Time of Day:** {scene.time_of_day}")
        if scene.weather:
            md_lines.append(f"**Weather:** {scene.weather}")
        
        md_lines.append("")
        
        # Physical world details
        if scene.physical_world:
            md_lines.extend([
                "**🌍 Physical World:**",
                ""
            ])
            pw = scene.physical_world
            
            if isinstance(pw, dict):
                if pw.get('architecture'):
                    arch = pw['architecture']
                    arch_str = ', '.join(arch) if isinstance(arch, list) else str(arch)
                    md_lines.append(f"- **Architecture:** {arch_str}")
                
                if pw.get('signs_text'):
                    signs = pw['signs_text']
                    if isinstance(signs, list):
                        md_lines.append(f"- **Signage:** {len(signs)} signs visible")
                        for sign in signs[:3]:  # Show first 3
                            if isinstance(sign, dict):
                                content = sign.get('content', '')
                                if content:
                                    md_lines.append(f"  - {content}")
                
                if pw.get('vehicles'):
                    vehicles = pw['vehicles']
                    if isinstance(vehicles, list):
                        md_lines.append(f"- **Vehicles:** {len(vehicles)} vehicles")
                        for vehicle in vehicles[:2]:  # Show first 2
                            if isinstance(vehicle, dict):
                                make = vehicle.get('make_model_estimate', vehicle.get('type', ''))
                                color = vehicle.get('color', '')
                                if make:
                                    md_lines.append(f"  - {color} {make}" if color else f"  - {make}")
            
            md_lines.append("")
        
        # Human subjects
        if scene.human_subjects:
            md_lines.extend([
                "**👥 Human Subjects:**",
                ""
            ])
            for subject in scene.human_subjects[:2]:  # Show first 2
                if isinstance(subject, dict):
                    demographics = subject.get('demographics', '')
                    clothing = subject.get('clothing', '')
                    if demographics:
                        md_lines.append(f"- {demographics}")
                    if clothing:
                        md_lines.append(f"  - Clothing: {clothing}")
            md_lines.append("")
        
        # Shots with ultra-detailed camera positioning
        if scene.shots:
            md_lines.extend([
                "### 🎥 Shot Details",
                ""
            ])
            
            for shot_idx, shot in enumerate(scene.shots, 1):
                md_lines.extend([
                    f"#### Shot {shot_idx}",
                    ""
                ])
                
                if shot.description:
                    md_lines.append(f"**Description:** {shot.description}")
                if shot.action:
                    md_lines.append(f"**Action:** {shot.action}")
                if shot.shot_type:
                    md_lines.append(f"**Shot Type:** {shot.shot_type}")
                
                md_lines.append("")
                
                # Ultra-precision camera positioning
                has_camera_data = any([
                    shot.camera_position,
                    shot.camera_angle_degrees,
                    shot.camera_distance_meters,
                    shot.camera_height_meters,
                    shot.camera_movement_trajectory,
                    shot.lens_focal_length,
                    shot.depth_of_field
                ])
                
                if has_camera_data:
                    md_lines.extend([
                        "**📐 Camera Positioning (Ultra-Precision):**",
                        ""
                    ])
                    
                    if shot.camera_position:
                        md_lines.append(f"- **Position:** {shot.camera_position}")
                    if shot.camera_angle_degrees:
                        md_lines.append(f"- **Angle:** {shot.camera_angle_degrees}")
                    if shot.camera_distance_meters:
                        md_lines.append(f"- **Distance:** {shot.camera_distance_meters}")
                    if shot.camera_height_meters:
                        md_lines.append(f"- **Height:** {shot.camera_height_meters}")
                    if shot.camera_movement_trajectory:
                        md_lines.append(f"- **Movement:** {shot.camera_movement_trajectory}")
                    if shot.lens_focal_length:
                        md_lines.append(f"- **Lens:** {shot.lens_focal_length}")
                    if shot.depth_of_field:
                        md_lines.append(f"- **Depth of Field:** {shot.depth_of_field}")
                    
                    md_lines.append("")
                
                # Spatial relationships
                if shot.subject_position_frame:
                    md_lines.extend([
                        f"**📍 Subject Position:** {shot.subject_position_frame}",
                        ""
                    ])
                
                if shot.spatial_relationships:
                    md_lines.extend([
                        f"**🗺 Spatial Relationships:**",
                        shot.spatial_relationships,
                        ""
                    ])
                
                if shot.motion_physics:
                    md_lines.extend([
                        f"**⚙️ Motion Physics:**",
                        shot.motion_physics,
                        ""
                    ])
        
        # Build comprehensive AI generation prompt
        md_lines.extend([
            "### 🤖 AI Generation Prompts",
            "",
            "#### Text-to-Image Prompt",
            "```"
        ])
        
        # Construct ultra-detailed prompt
        prompt_parts = []
        
        # Scene and description
        if scene.description:
            prompt_parts.append(scene.description)
        
        # Location context
        prompt_parts.append(f"Location: {scene.location}")
        
        # Camera details from first shot
        if scene.shots:
            shot = scene.shots[0]
            if shot.shot_type:
                prompt_parts.append(f"Shot: {shot.shot_type}")
            if shot.camera_position:
                prompt_parts.append(f"Camera: {shot.camera_position}")
            if shot.spatial_relationships:
                prompt_parts.append(f"Spatial: {shot.spatial_relationships}")
        
        # Lighting
        if scene.lighting:
            prompt_parts.append(f"Lighting: {scene.lighting}")
        
        # Film stock
        if report.film_stock_look:
            prompt_parts.append(f"Film Stock: {report.film_stock_look}")
        
        # Style
        if report.overall_style:
            prompt_parts.append(f"Style: {report.overall_style}")
        
        # Mood
        if scene.mood:
            prompt_parts.append(f"Mood: {scene.mood}")
        
        full_prompt = ". ".join(prompt_parts) + "."
        
        md_lines.extend([
            full_prompt,
            "```",
            "",
        ])
        
        # Video prompt
        md_lines.extend([
            "#### Image-to-Video Prompt",
            "```"
        ])
        
        video_prompt_parts = []
        
        if scene.description:
            video_prompt_parts.append(scene.description)
        
        # Camera movement
        if scene.shots and scene.shots[0].camera_movement:
            video_prompt_parts.append(f"Camera movement: {scene.shots[0].camera_movement}")
        if scene.shots and scene.shots[0].camera_movement_trajectory:
            video_prompt_parts.append(f"Movement: {scene.shots[0].camera_movement_trajectory}")
        
        # Motion physics
        if scene.shots and scene.shots[0].motion_physics:
            video_prompt_parts.append(f"Motion: {scene.shots[0].motion_physics}")
        
        # Film look
        if report.film_stock_look:
            video_prompt_parts.append(f"Film look: {report.film_stock_look}")
        
        video_prompt = ". ".join(video_prompt_parts) + "."
        
        md_lines.extend([
            video_prompt,
            "```",
            "",
            "---",
            ""
        ])
    
    # Write markdown file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    logger.info(f"Generated detailed markdown: {output_path}")
