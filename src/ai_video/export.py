"""Export utilities for generating consolidated prompt files."""

from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .models import VideoReport, Scene, Shot, PromptBundle, CameraShotBreakdown
from .logging import get_logger

logger = get_logger(__name__)


def generate_detailed_markdown(report: VideoReport, output_path: Path, bundles: Optional[List[PromptBundle]] = None) -> None:
    """
    Generate ultra-detailed consolidated markdown file with all scene information.
    
    Args:
        report: VideoReport containing all analysis data
        output_path: Path where markdown file should be saved
        bundles: Optional list of PromptBundles with first+last frame info
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
    ]
    
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
                    if isinstance(arch, list):
                        # Convert all items to strings (handle both str and dict)
                        arch_strs = [str(a) if not isinstance(a, dict) else a.get('description', str(a)) for a in arch]
                        arch_str = ', '.join(arch_strs)
                    else:
                        arch_str = str(arch)
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
                        md_lines.append(f"- **Vehicles:**")
                        for vehicle in vehicles:  # Show ALL vehicles with details
                            if isinstance(vehicle, dict):
                                # Get make/model with priority order
                                make_model = (vehicle.get('make_model') or 
                                            vehicle.get('make_model_estimate') or 
                                            vehicle.get('model') or 
                                            vehicle.get('model_guess') or 
                                            vehicle.get('type', 'Vehicle'))
                                
                                # Build complete vehicle description
                                vehicle_parts = []
                                color = vehicle.get('color', '')
                                year = vehicle.get('year') or vehicle.get('generation')
                                brand = vehicle.get('brand')
                                
                                # Combine brand and make_model intelligently
                                if brand and make_model and brand.lower() not in make_model.lower():
                                    vehicle_desc = f"{color} {brand} {make_model}" if color else f"{brand} {make_model}"
                                elif color:
                                    vehicle_desc = f"{color} {make_model}"
                                else:
                                    vehicle_desc = make_model
                                
                                if year:
                                    vehicle_desc += f" ({year})"
                                
                                # Add position/description if available
                                desc = vehicle.get('description')
                                if desc and desc != 'Not visible':
                                    vehicle_desc += f" - {desc}"
                                
                                md_lines.append(f"  - {vehicle_desc}")
                            elif isinstance(vehicle, str) and vehicle != 'Not visible':
                                md_lines.append(f"  - {vehicle}")
            
            md_lines.append("")
        
        # Human subjects - ENHANCED with full details
        if scene.human_subjects:
            md_lines.extend([
                "**👥 Human Subjects:**",
                ""
            ])
            for subject in scene.human_subjects:  # Show ALL subjects
                if isinstance(subject, dict):
                    # Demographics
                    demographics = subject.get('demographics')
                    if demographics:
                        if isinstance(demographics, dict):
                            demo_parts = []
                            if demographics.get('age_group'):
                                demo_parts.append(demographics['age_group'])
                            if demographics.get('gender_presentation'):
                                demo_parts.append(demographics['gender_presentation'])
                            if demographics.get('ethnicity'):
                                demo_parts.append(demographics['ethnicity'])
                            md_lines.append(f"- {', '.join(demo_parts)}")
                        else:
                            md_lines.append(f"- {demographics}")
                    
                    # Physical description
                    physical = subject.get('physical_description')
                    if physical and physical != 'Not visible':
                        if isinstance(physical, dict):
                            phys_parts = []
                            for key in ['build', 'height', 'hair', 'skin_tone']:
                                val = physical.get(key)
                                if val and val != 'Not visible':
                                    phys_parts.append(f"{key}: {val}")
                            if phys_parts:
                                md_lines.append(f"  - Physical: {', '.join(phys_parts)}")
                        elif physical:
                            md_lines.append(f"  - Physical: {physical}")
                    
                    # Clothing - FULL DETAILS
                    clothing = subject.get('clothing')
                    if clothing:
                        if isinstance(clothing, dict):
                            # Filter out "Not visible" values
                            clothing_parts = []
                            for layer in ['upper_body', 'mid_layer', 'outer_layer', 'lower_body', 'footwear', 'accessories']:
                                val = clothing.get(layer)
                                if val and val != 'Not visible' and 'not visible' not in str(val).lower():
                                    clothing_parts.append(f"{layer.replace('_', ' ').title()}: {val}")
                            if clothing_parts:
                                md_lines.append(f"  - Clothing: {'; '.join(clothing_parts)}")
                        else:
                            if str(clothing) != 'Not visible' and 'not visible' not in str(clothing).lower():
                                md_lines.append(f"  - Clothing: {clothing}")
                    
                    # Action
                    action = subject.get('action')
                    if action and action != 'Not visible':
                        md_lines.append(f"  - Action: {action}")
            md_lines.append("")
        
        # Shots with cinematography breakdowns
        if scene.shots:
            md_lines.extend([
                "### 🎥 Shot Details",
                ""
            ])

            scene_breakdowns = []
            bundle_breakdowns = None
            if bundles and (scene_idx - 1) < len(bundles):
                bundle_candidate = bundles[scene_idx - 1]
                if getattr(bundle_candidate, "camera_breakdowns", None):
                    bundle_breakdowns = bundle_candidate.camera_breakdowns

            source_breakdowns = bundle_breakdowns or getattr(scene, "camera_breakdowns", None) or []

            for item in source_breakdowns:
                if isinstance(item, dict):
                    try:
                        scene_breakdowns.append(CameraShotBreakdown(**item))
                    except Exception:
                        continue
                elif isinstance(item, CameraShotBreakdown):
                    scene_breakdowns.append(item)

            for shot_idx, shot in enumerate(scene.shots, 1):
                md_lines.extend([
                    f"#### Shot {shot_idx}",
                    ""
                ])

                if shot.description:
                    md_lines.append(f"**Description:** {shot.description}")
                if shot.action:
                    md_lines.append(f"**Action:** {shot.action}")

                breakdown = scene_breakdowns[shot_idx - 1] if shot_idx - 1 < len(scene_breakdowns) else None

                if breakdown:
                    md_lines.append("")
                    md_lines.extend([
                        "**🎯 Cinematography Breakdown:**",
                        ""
                    ])

                    camera_components = []
                    if breakdown.camera_shot_type:
                        camera_components.append(f"Shot Type: {breakdown.camera_shot_type}")
                    if breakdown.camera_angle:
                        camera_components.append(f"Angle: {breakdown.camera_angle}")
                    if breakdown.camera_height:
                        camera_components.append(f"Height: {breakdown.camera_height}")
                    if breakdown.camera_distance:
                        camera_components.append(f"Distance: {breakdown.camera_distance}")
                    if breakdown.framing_style:
                        camera_components.append(f"Framing: {breakdown.framing_style}")
                    if breakdown.lens_type_estimate:
                        camera_components.append(f"Lens: {breakdown.lens_type_estimate}")
                    if breakdown.depth_of_field:
                        camera_components.append(f"Depth of Field: {breakdown.depth_of_field}")
                    if breakdown.camera_motion and breakdown.camera_motion.lower() != "static":
                        camera_components.append(f"Camera Motion: {breakdown.camera_motion}")

                    if camera_components:
                        md_lines.append("- **Camera:** " + "; ".join(camera_components))

                    lighting_bits = []
                    if breakdown.lighting_style.key_light:
                        lighting_bits.append(f"Key: {breakdown.lighting_style.key_light}")
                    if breakdown.lighting_style.fill_light:
                        lighting_bits.append(f"Fill: {breakdown.lighting_style.fill_light}")
                    if breakdown.lighting_style.practical_lights:
                        lighting_bits.append(f"Practicals: {breakdown.lighting_style.practical_lights}")
                    if breakdown.lighting_style.mood:
                        lighting_bits.append(f"Mood: {breakdown.lighting_style.mood}")
                    if lighting_bits:
                        md_lines.append("- **Lighting:** " + "; ".join(lighting_bits))

                    if breakdown.composition_notes:
                        md_lines.append(f"- **Composition Notes:** {breakdown.composition_notes}")
                    if breakdown.set_design_notes:
                        md_lines.append(f"- **Set Design Notes:** {breakdown.set_design_notes}")
                    if breakdown.cinematic_purpose:
                        md_lines.append(f"- **Purpose:** {breakdown.cinematic_purpose}")
                    if breakdown.recreation_guidance:
                        md_lines.append(f"- **Recreation Guidance:** {breakdown.recreation_guidance}")

                    md_lines.append("")
                else:
                    md_lines.append("")
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
                            "**📐 Camera Positioning (Source Data):**",
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

                # Spatial relationships – avoid duplication if captured in composition notes
                composition_text = breakdown.composition_notes.lower() if breakdown and breakdown.composition_notes else ""

                if shot.subject_position_frame and shot.subject_position_frame.lower() not in composition_text:
                    md_lines.extend([
                        f"**📍 Subject Position:** {shot.subject_position_frame}",
                        ""
                    ])

                if shot.spatial_relationships and shot.spatial_relationships.lower() not in composition_text:
                    md_lines.extend([
                        "**🗺 Spatial Relationships:**",
                        shot.spatial_relationships,
                        ""
                    ])

                if shot.motion_physics:
                    md_lines.extend([
                        "**⚙️ Motion Physics:**",
                        shot.motion_physics,
                        ""
                    ])
        
        # Build comprehensive AI generation prompts
        md_lines.extend([
            "### 🤖 AI Generation Prompts (Kling 2.1 Pro Compatible)",
            ""
        ])
        
        # Check if this scene should use first+last frame approach
        # Use data from the prompt bundle if available, otherwise fallback to heuristic
        use_first_last = False
        first_frame_prompt = None
        last_frame_prompt = None
        reasoning = None
        
        if bundles and (scene_idx - 1) < len(bundles):
            bundle = bundles[scene_idx - 1]
            if bundle.video_prompts:
                video_prompt = bundle.video_prompts[0]
                use_first_last = video_prompt.use_first_last_frame or False
                first_frame_prompt = video_prompt.first_frame_prompt
                last_frame_prompt = video_prompt.last_frame_prompt
                reasoning = video_prompt.first_last_frame_reasoning
        
        # Fallback heuristic if no bundle data available
        if bundles is None and scene.shots and len(scene.shots) > 0:
            shot = scene.shots[0]
            if scene.duration >= 2.0:
                action = shot.get('action', '').lower() if isinstance(shot, dict) else (getattr(shot, 'action', '') or '').lower()
                camera_movement = shot.get('camera_movement', '').lower() if isinstance(shot, dict) else (getattr(shot, 'camera_movement', '') or '').lower()
                movement_keywords = ['walk', 'move', 'turn', 'ride', 'approach', 'exit', 'enter']
                camera_keywords = ['track', 'dolly', 'crane', 'follow', 'orbit']
                has_movement = any(kw in action for kw in movement_keywords)
                has_camera_movement = any(kw in camera_movement for kw in camera_keywords)
                use_first_last = has_movement or has_camera_movement or scene.duration >= 4.0
        
        if use_first_last and scene.duration >= 2.0:
            # Show recommendation with reasoning if available
            recommendation_text = reasoning if reasoning else f"This scene ({scene.duration:.1f}s with significant movement/transformation) will benefit from Kling 2.1 Pro's first+last frame feature."
            
            md_lines.extend([
                "**💡 Recommendation: Use First+Last Frame Approach**",
                "",
                recommendation_text,
                "",
                "#### First Frame Prompt (Text-to-Image)",
                "```"
            ])
        else:
            md_lines.extend([
                "#### Text-to-Image Prompt",
                "```"
            ])
        
        # Use pre-generated prompt from bundle if available, otherwise construct it
        if use_first_last and first_frame_prompt:
            # Use the intelligently generated first frame prompt
            full_prompt = first_frame_prompt
        else:
            # Fallback: Construct ultra-detailed prompt
            prompt_parts = []
            
            # Scene and description
            if scene.description:
                prompt_parts.append(scene.description)
            
            # Human subjects - FULL clothing and physical details
            if scene.human_subjects:
                human_parts = []
                for subject in scene.human_subjects:
                    if isinstance(subject, dict):
                        subject_desc_parts = []
                        
                        # Demographics
                        demographics = subject.get('demographics')
                        if demographics:
                            if isinstance(demographics, dict):
                                demo_strs = []
                                if demographics.get('age_group'):
                                    demo_strs.append(demographics['age_group'])
                                if demographics.get('gender_presentation'):
                                    demo_strs.append(demographics['gender_presentation'])
                                if demographics.get('ethnicity'):
                                    demo_strs.append(demographics['ethnicity'])
                                if demo_strs:
                                    subject_desc_parts.append(' '.join(demo_strs))
                            else:
                                subject_desc_parts.append(str(demographics))
                        
                        # Physical description
                        physical = subject.get('physical_description')
                        if physical and physical != 'Not visible':
                            if isinstance(physical, dict):
                                phys_strs = []
                                for key in ['build', 'height', 'hair', 'skin_tone']:
                                    val = physical.get(key)
                                    if val and val != 'Not visible':
                                        phys_strs.append(val)
                                if phys_strs:
                                    subject_desc_parts.append(', '.join(phys_strs))
                            elif physical:
                                subject_desc_parts.append(str(physical))
                        
                        # Clothing - ALL details
                        clothing = subject.get('clothing')
                        if clothing:
                            if isinstance(clothing, dict):
                                clothing_strs = []
                                for layer in ['upper_body', 'mid_layer', 'outer_layer', 'lower_body', 'footwear', 'accessories']:
                                    val = clothing.get(layer)
                                    if val and val != 'Not visible' and 'not visible' not in str(val).lower():
                                        clothing_strs.append(str(val))
                                if clothing_strs:
                                    subject_desc_parts.append('wearing ' + ', '.join(clothing_strs))
                            else:
                                if str(clothing) != 'Not visible' and 'not visible' not in str(clothing).lower():
                                    subject_desc_parts.append(f"wearing {clothing}")
                        
                        if subject_desc_parts:
                            human_parts.append(', '.join(subject_desc_parts))
                
                if human_parts:
                    prompt_parts.append('Human subjects: ' + '; '.join(human_parts))
            
            # Physical World - vehicles with full details (color, make, model)
            if scene.physical_world:
                pw = scene.physical_world
                if isinstance(pw, dict):
                    # Vehicles with COMPLETE details
                    if pw.get('vehicles'):
                        vehicles = pw['vehicles']
                        if isinstance(vehicles, list):
                            vehicle_descs = []
                            for vehicle in vehicles:
                                if isinstance(vehicle, dict):
                                    # Get make/model with priority order
                                    make_model = (vehicle.get('make_model') or 
                                                vehicle.get('make_model_estimate') or 
                                                vehicle.get('model') or 
                                                vehicle.get('model_guess') or 
                                                vehicle.get('type', ''))
                                    
                                    # Build complete vehicle description
                                    color = vehicle.get('color', '')
                                    year = vehicle.get('year') or vehicle.get('generation')
                                    brand = vehicle.get('brand')
                                    
                                    # Combine brand and make_model intelligently
                                    if brand and make_model and brand.lower() not in make_model.lower():
                                        vehicle_desc = f"{color} {brand} {make_model}" if color else f"{brand} {make_model}"
                                    elif color and make_model:
                                        vehicle_desc = f"{color} {make_model}"
                                    elif make_model:
                                        vehicle_desc = make_model
                                    elif color:
                                        vehicle_desc = f"{color} vehicle"
                                    else:
                                        continue
                                    
                                    if year:
                                        vehicle_desc += f" ({year})"
                                    
                                    vehicle_descs.append(vehicle_desc.strip())
                                elif isinstance(vehicle, str) and vehicle != 'Not visible':
                                    vehicle_descs.append(vehicle)
                            
                            if vehicle_descs:
                                prompt_parts.append('Vehicles: ' + ', '.join(vehicle_descs))
                    
                    # Architecture
                    if pw.get('architecture'):
                        arch = pw['architecture']
                        if isinstance(arch, list):
                            arch_strs = [str(a) if not isinstance(a, dict) else a.get('description', str(a)) for a in arch]
                            arch_str = ', '.join(arch_strs)
                        else:
                            arch_str = str(arch)
                        if arch_str:
                            prompt_parts.append(f"Architecture: {arch_str}")
                    
                    # Signage
                    if pw.get('signs_text'):
                        signs = pw['signs_text']
                        if isinstance(signs, list):
                            sign_texts = []
                            for sign in signs[:3]:  # Include up to 3 signs
                                if isinstance(sign, dict):
                                    content = sign.get('content', '')
                                    if content:
                                        sign_texts.append(content)
                                elif isinstance(sign, str):
                                    sign_texts.append(sign)
                            if sign_texts:
                                prompt_parts.append('Signage: ' + ', '.join(sign_texts))
            
            # Location context
            prompt_parts.append(f"Location: {scene.location}")
            
            # CAMERA POSITIONING - CRITICAL FOR ACCURATE RECREATION
            # Include ALL camera details from first shot to ensure exact positioning match
            if scene.shots:
                shot = scene.shots[0]
                
                # Build comprehensive camera positioning description
                camera_parts = []
                
                # Shot type (wide, medium, close-up)
                if shot.shot_type:
                    camera_parts.append(f"{shot.shot_type} shot")
                
                # Exact camera position (most important!)
                if shot.camera_position:
                    camera_parts.append(shot.camera_position)
                
                # Camera angle in degrees
                if shot.camera_angle_degrees:
                    camera_parts.append(f"angle: {shot.camera_angle_degrees}")
                
                # Distance from subject
                if shot.camera_distance_meters:
                    camera_parts.append(f"distance: {shot.camera_distance_meters}")
                
                # Camera height from ground
                if shot.camera_height_meters:
                    camera_parts.append(f"height: {shot.camera_height_meters}")
                
                # Lens focal length (affects field of view and perspective)
                if shot.lens_focal_length:
                    camera_parts.append(f"lens: {shot.lens_focal_length}")
                
                # Depth of field (affects what's in focus)
                if shot.depth_of_field:
                    camera_parts.append(f"DOF: {shot.depth_of_field}")
                
                if camera_parts:
                    prompt_parts.append(f"Camera: {', '.join(camera_parts)}")
                
                # Subject position in frame (where subject appears in the composition)
                if shot.subject_position_frame:
                    prompt_parts.append(f"Subject position: {shot.subject_position_frame}")
                
                # Spatial relationships (3D space understanding)
                if shot.spatial_relationships:
                    prompt_parts.append(f"Spatial: {shot.spatial_relationships}")
            
            # Lighting
            if scene.lighting:
                prompt_parts.append(f"Lighting: {scene.lighting}")

            # Style / Mood scoped to the scene
            if scene.style:
                prompt_parts.append(f"Style: {scene.style}")
            if scene.mood:
                prompt_parts.append(f"Mood: {scene.mood}")
            
            full_prompt = ". ".join(prompt_parts) + "."
        
        md_lines.extend([
            full_prompt,
            "```",
            ""
        ])
        
        # If using first+last frame, add last frame prompt
        if use_first_last and scene.duration >= 2.0:
            # Use pre-generated last frame prompt if available, otherwise construct it
            if last_frame_prompt:
                final_last_prompt = last_frame_prompt
            else:
                # Fallback: Generate last frame prompt (modify subject for end state)
                last_frame_parts = []
                
                # Modify description for end state
                if scene.description:
                    desc = scene.description
                    # Add "at end of movement" or "having completed action"
                    if scene.shots and scene.shots[0].action:
                        action = (scene.shots[0].action or '').lower()
                        if any(kw in action for kw in ['walk', 'move', 'approach']):
                            desc += " having completed movement"
                        elif 'turn' in action:
                            desc += " having turned"
                        else:
                            desc += " at end of action"
                    last_frame_parts.append(desc)
                
                # Keep same location, lighting, style
                last_frame_parts.append(f"Location: {scene.location}")
                if scene.shots and scene.shots[0].camera_position:
                    # Extract end position if mentioned
                    cam_pos = scene.shots[0].camera_position
                    if "to" in cam_pos.lower():
                        last_frame_parts.append(f"Camera: {cam_pos.split('to')[-1].strip() if 'to' in cam_pos else cam_pos}")
                if scene.lighting:
                    last_frame_parts.append(f"Lighting: {scene.lighting}")
                if scene.style:
                    last_frame_parts.append(f"Style: {scene.style}")
                
                final_last_prompt = ". ".join(last_frame_parts) + "."
            
            md_lines.extend([
                "",
                "#### Last Frame Prompt (Text-to-Image)",
                "```",
                final_last_prompt,
                "```",
                "",
                "**Workflow:** Generate both frames with text-to-image model (e.g., SeaArt, Midjourney, DALL-E), then use both as input to Kling 2.1 Pro for video generation.",
                ""
            ])
        else:
            md_lines.append("")
        
        # Video prompt (or note about first+last frame)
        if use_first_last:
            md_lines.extend([
                "#### Video Generation (Kling 2.1 Pro)",
                "Use first+last frame mode with the two generated images above.",
                ""
            ])
        else:
            md_lines.extend([
                "#### Image-to-Video Prompt",
                "```"
            ])
        
        # Only generate standard video prompt if NOT using first+last frame
        if not use_first_last:
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
            
            # Style / mood scoped to the scene
            if scene.style:
                video_prompt_parts.append(f"Style: {scene.style}")
            if scene.mood:
                video_prompt_parts.append(f"Mood: {scene.mood}")

            video_prompt = ". ".join(video_prompt_parts) + "."
            
            md_lines.extend([
                video_prompt,
                "```",
                ""
            ])
        
        md_lines.extend([
            "---",
            ""
        ])
    
    # Write markdown file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    logger.info(f"Generated detailed markdown: {output_path}")
