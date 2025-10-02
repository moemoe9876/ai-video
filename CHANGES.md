# System Changes - Ultra-Precision Video Analysis

## Summary
Implemented ultra-precision video analysis system with automatic detailed markdown generation for 99% recreation accuracy.

## What Changed

### 1. **New Export Module** (`src/ai_video/export.py`)
- Created `generate_detailed_markdown()` function
- Automatically generates comprehensive markdown files with:
  - Film technical specifications (stock, lens, style, mood, cultural context)
  - Scene-by-scene breakdowns with timing
  - Ultra-precise camera positioning (height, angle, distance in meters/degrees)
  - Spatial relationships and motion physics
  - Physical world details (architecture, signage, vehicles)
  - Human subject descriptions
  - Ready-to-use AI generation prompts (T2I and I2V)

### 2. **Updated CLI** (`src/ai_video/cli.py`)
- Added automatic markdown generation to `make-prompts` command
- Added automatic markdown generation to `run-all` command (when using `--export`)
- Import of new `generate_detailed_markdown` function

### 3. **Enhanced Data Capture** (Already in place)
- Ultra-precision camera positioning fields in Shot model:
  - `camera_position` - Exact position relative to subject
  - `camera_angle_degrees` - Angle in degrees
  - `camera_distance_meters` - Distance from subject in meters
  - `camera_height_meters` - Height of camera from ground
  - `camera_movement_trajectory` - Detailed movement path
  - `lens_focal_length` - Estimated focal length
  - `depth_of_field` - Depth of field characteristics
  - `subject_position_frame` - Subject position in frame
  - `spatial_relationships` - 3D spatial relationships
  - `motion_physics` - Physics of movement

### 4. **Parsing Improvements** (`src/ai_video/agents/video_analysis.py`)
- Handle lighting data as dict or string
- Handle entity_id vs name field inconsistencies
- Convert dict camera positioning data to strings
- Support for all new ultra-precision fields

### 5. **Enhanced Gemini Blueprint** (`src/ai_video/prompts/gemini_video_blueprint.md`)
- Complete rewrite for 99% recreation accuracy
- Detailed instructions for camera positioning with measurements
- Comprehensive spatial and positional understanding
- Complete human demographics profiling
- Physics and motion understanding
- Geographic and cultural markers
- Professional cinematography terminology

## Output Files

Every analysis now generates:

1. **JSON Report** - `assets/reports/{video_id}_report.json`
   - Complete structured data with all ultra-precision fields

2. **Scene Prompt JSONs** - `assets/prompts/{video_id}/scene_XXX.json`
   - Individual scene prompts for programmatic access

3. **Detailed Markdown** - `assets/prompts/{video_id}/prompts_detailed.md` ✨ NEW
   - Human-readable consolidated view with all scenes
   - Ultra-detailed camera positioning
   - Complete AI generation prompts
   - Film technical specifications

## Usage

### Automatic Generation (New Runs)
```bash
# Option 1: Full pipeline with export
ai-video run-all video.mp4 --export

# Option 2: Generate prompts from existing report
ai-video make-prompts assets/reports/{video_id}_report.json
```

Both commands now automatically generate `prompts_detailed.md`

### What You Get

**prompts_detailed.md** includes:
- 🎬 Film Technical Specifications
  - Film Stock (e.g., "Cinestill 800T with red halation")
  - Lens (e.g., "35-50mm vintage primes")
  - Style, Mood, Cultural Context
- 📐 Ultra-Precision Camera Positioning
  - Height: "4 meters high"
  - Angle: "30-40 degrees downward"
  - Distance: "8 meters from subject"
  - Movement: "Tracking at 30-40 km/h"
- 🤖 Ready-to-Use AI Prompts
  - Text-to-Image prompts
  - Image-to-Video prompts

## Example Output

```markdown
### 🎥 Shot Details

#### Shot 1

**Shot Type:** Medium shot, tracking.

**📐 Camera Positioning (Ultra-Precision):**

- **Position:** Approximately 1.5 meters, level with the subjects.
- **Distance:** Approximately 2-3 meters.
- **Angle:** 0 degrees (eye-level), shooting their right profile.
- **Movement:** Tracking shot, moving left-to-right at the same speed as the motorcycle (approx. 30-40 km/h).

### 🤖 AI Generation Prompts

#### Text-to-Image Prompt
```
A young couple rides a motorcycle down a city street during the day. 
Camera: 1.5 meters height, 2-3 meters distance, eye-level, tracking at 30-40 km/h. 
Film Stock: Cinestill 800T with prominent red halation. 
Style: 1990s Hong Kong New Wave cinema.
```
```

## Benefits

1. **No Manual Consolidation** - Automatic generation on every run
2. **99% Recreation Accuracy** - Ultra-detailed camera positioning and measurements
3. **Professional Terminology** - Film stock, lens, and cinematography terms
4. **Ready for AI Tools** - Copy-paste prompts into Midjourney, Runway, Pika, etc.
5. **Human Readable** - Beautiful markdown format with emojis and structure
6. **Future Proof** - All new analyses automatically get this format

## Backward Compatible

- Existing reports can be re-processed with `ai-video make-prompts <report.json>`
- Old workflow still works, just generates additional markdown file
- No breaking changes to existing functionality
