# AI Video - Video Analysis and Prompt Generation

AI-powered video analysis and prompt generation system for recreating videos with generative AI models. This tool uses Gemini 2.5 for video understanding and generates structured prompts for text-to-image, image-to-video, and text-to-video AI generation.

## Features

### 🎯 Ultra-Precision Video Analysis (99% Recreation Accuracy)
- **Exact Camera Positioning**: Height, angle, distance in meters and degrees
- **Spatial Relationships**: Complete 3D spatial mapping and depth layers
- **Motion Physics**: Speed, momentum, weight analysis with measurements
- **Human Demographics**: Detailed ethnicity, age, clothing, and positioning
- **Film Technical Details**: Stock characteristics, lens specs, color science
- **Cultural Context**: Geographic, temporal, and cultural markers

### 🤖 AI-Optimized Prompt Generation
- **Automatic Detailed Markdown**: Beautiful consolidated prompts with all scenes
- **Text-to-Image Prompts**: Ready for Midjourney, Stable Diffusion, DALL-E
- **Image-to-Video Prompts**: Optimized for Runway, Pika, Stable Video
- **Professional Terminology**: Film stock names, lens specs, lighting standards

### 🎬 Comprehensive Analysis Pipeline
- **Scene Segmentation**: Automatic breakdown into scenes and shots
- **Gemini 2.5 Integration**: Deep analysis with Pro/Flash models
- **Structured JSON Reports**: Complete data for programmatic access
- **Multiple Export Formats**: Markdown, JSON, and shot lists
- **YouTube Support**: Direct analysis of YouTube URLs
- **File API**: Automatic handling of large videos
- **Pipeline Management**: Complete automated workflow with checkpoints

### 🎨 Creative Prompt Reimagination
- **Variant Generator**: Produce 3–5 creative reinterpretations for every scene
- **Global Style Profiles**: Apply user directives or auto-selected cinematic directions
- **JSON + Markdown Outputs**: Emits `variant_prompts.json` and `variant_report.md`
- **Standalone Agent**: Run via module CLI or `ai-video reimagine`

## Installation

### Prerequisites

- Python 3.10 or higher
- FFmpeg (for video processing)
- Google API key with Gemini access

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd ai-video
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install -e .
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and set your GOOGLE_API_KEY
```

5. **Verify installation:**
```bash
ai-video doctor
```

## Quick Start

### Analyze a Video

```bash
# Analyze a local video file
ai-video analyze --input path/to/video.mp4

# Analyze a YouTube video
ai-video analyze --input "https://www.youtube.com/watch?v=VIDEO_ID"

# Analyze with custom settings
ai-video analyze --input video.mp4 --start 10s --end 60s --fps 2
```

### Generate Prompts

```bash
# Generate prompts from an analysis report
ai-video make-prompts assets/reports/VIDEO_ID_report.json
```

### Run Complete Pipeline

```bash
# Analyze video and generate prompts in one command
ai-video run-all --input path/to/video.mp4

# Skip export step
ai-video run-all --input video.mp4 --no-export
```

### Export Prompts

```bash
# Export all formats (Markdown, JSON, shot list)
ai-video export-prompts VIDEO_ID

# Export specific format
ai-video export-prompts VIDEO_ID --format md
```

## Usage Examples

### Analyze a Short Commercial

```bash
ai-video analyze --input commercial.mp4 --id my_commercial
```

Output:
- Analysis report: `assets/reports/my_commercial_report.json`
- Contains: scenes, shots, entities, timing, camera movements, lighting

### Generate Prompts for AI Recreation

```bash
ai-video make-prompts assets/reports/my_commercial_report.json
```

Output:
- **`prompts_detailed.md`** ✨ - Ultra-detailed consolidated markdown with all scenes
- Scene JSONs: `scene_001.json`, `scene_002.json`, etc.
- Each contains: T2I and I2V prompts with complete technical details

### Export for Creative Teams

```bash
ai-video export-prompts my_commercial
```

Output:
- `assets/prompts/my_commercial/prompts.md` - Human-readable prompts
- `assets/prompts/my_commercial/prompts.json` - Machine-readable format
- `assets/prompts/my_commercial/shot_list.md` - Shot-by-shot breakdown

### Reimagine Existing Prompts

```bash
# Auto-select a cohesive creative direction
ai-video reimagine --input assets/prompts/VIDEO_ID/prompts_detailed.md

# Force a global directive and variant count
ai-video reimagine \
  --input assets/prompts/VIDEO_ID/prompts_detailed.md \
  --style "anime cyberpunk tokyo" \
  --num-variants 4

# Layer additional free-form instructions across all variants
ai-video reimagine \
  --input assets/prompts/VIDEO_ID/prompts_detailed.md \
  --user-prompt "Highlight the humid summer night air and the couple's unspoken tension"

# Run the standalone agent module directly
python -m ai_video.agents.reimagination_agent \
  --input assets/prompts/VIDEO_ID/prompts_detailed.md \
  --output assets/prompts/VIDEO_ID
```

Output:
- `variant_prompts.json` – Structured `ReimaginationResult` with per-scene image + video variants
- `variant_report.md` – Concise operator summary grouped by scene (shows both prompt types and metadata)
- User-supplied directives are respected across every scene; omit `--style` to let the agent choose a cohesive look and document it in the global style profile. Add `--user-prompt` for extra narrative or stylistic cues that should apply to all variants.

### Analyze YouTube Video Clip

```bash
ai-video analyze \
  --input "https://www.youtube.com/watch?v=VIDEO_ID" \
  --start 30s \
  --end 90s \
  --id youtube_clip
```

## Output Structure

Every analysis generates comprehensive output files:

### 1. JSON Report (`assets/reports/{video_id}_report.json`)
Complete structured data including:
- Video metadata (duration, resolution, fps)
- Film stock characteristics and lens details
- Scene-by-scene breakdown with timing
- Ultra-precision camera positioning (meters, degrees)
- Spatial relationships and motion physics
- Human subjects with demographics
- Physical world inventory

### 2. Ultra-Detailed Markdown (`assets/prompts/{video_id}/prompts_detailed.md`) ✨
**Automatically generated** - Human-readable consolidated view with:

```markdown
## 🎬 Film Technical Specifications
- Film Stock: "Cinestill 800T with red halation around lights"
- Lens: "35-50mm vintage primes with soft bokeh"
- Style: "Wong Kar-wai inspired, 1990s Hong Kong New Wave"

## Scene 1

### 🎥 Shot Details

**📐 Camera Positioning (Ultra-Precision):**
- Position: Approximately 4 meters high from upper floor window
- Angle: 30-40 degrees downward (high angle)
- Distance: Starts at 8 meters, subject walks to 5 meters
- Movement: Static, locked-off shot, perfectly stable

**🗺 Spatial Relationships:**
Foreground: Van at 2 meters. Midground: Subject at 8 meters center-right. 
Background: Buildings 15-25 meters, storefronts 10-15 meters.

### 🤖 AI Generation Prompts

#### Text-to-Image Prompt
```
Young man walking through brightly lit alley at night. Camera: 4 meters high, 
30-40 degree downward angle, 8 meters distance. Film: Cinestill 800T with 
prominent halation. Style: 1990s Hong Kong cinema aesthetic.
```

#### Image-to-Video Prompt
```
Young man walks forward through alley. Static camera locked at 4 meters high. 
Film look: Cinestill 800T with grain and red halation.
```
```

### 3. Scene JSON Files (`assets/prompts/{video_id}/scene_XXX.json`)
Individual scene data for programmatic access:
- Timing and duration
- Image and video prompts
- Camera specifications
- Lighting and style details

## Configuration

### config.yaml

```yaml
# Asset directories
assets_dir: "assets"
inputs_dir: "assets/inputs"
reports_dir: "assets/reports"
prompts_dir: "assets/prompts"
runs_dir: "assets/runs"
logs_dir: "assets/logs"

# Gemini configuration
gemini:
  model: "gemini-2.0-flash-exp"  # or "gemini-2.5-pro"
  max_retries: 3
  timeout: 120
  file_api_threshold_mb: 20

# Video processing
video:
  default_fps: 1
  max_duration_seconds: 3600
  supported_formats:
    - mp4
    - mpeg
    - mov
    - avi
    - webm

# Prompt generation
prompts:
  include_timestamps: true
  include_camera_details: true
  include_lighting: true
  include_style: true
  max_prompt_length: 500

# Pipeline
pipeline:
  checkpoint_enabled: true
  retry_on_failure: true
  max_retries: 3
```

### Environment Variables

Create a `.env` file:

```env
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional
ASSETS_DIR=assets
MODEL_GEMINI=gemini-2.0-flash-exp
LOG_LEVEL=INFO
```

## Output Structure

```
assets/
├── inputs/          # Place your input videos here
├── reports/         # Video analysis reports
│   └── {video_id}_report.json
├── prompts/         # Generated prompts
│   └── {video_id}/
│       ├── scene_001.json
│       ├── scene_002.json
│       ├── prompts.md
│       ├── prompts.json
│       └── shot_list.md
├── runs/            # Pipeline run manifests
│   └── run_{timestamp}.json
└── logs/            # Application logs
```

## CLI Commands

### `ai-video analyze`

Analyze a video and generate a structured report.

**Options:**
- `--input`: Path to video file or YouTube URL (required)
- `--id`: Custom video ID (optional)
- `--start`: Start offset (e.g., "10s", "1m30s")
- `--end`: End offset
- `--fps`: Frames per second for sampling
- `--model`: Gemini model to use
- `--verbose, -v`: Verbose output

### `ai-video make-prompts`

Generate prompts from a video analysis report.

**Options:**
- `report`: Path to report JSON file (required)
- `--verbose, -v`: Verbose output

### `ai-video run-all`

Run the complete pipeline: analyze video and generate prompts.

**Options:**
- `--input`: Path to video file or YouTube URL (required)
- `--id`: Custom video ID
- `--run-id`: Custom run ID
- `--start`: Start offset
- `--end`: End offset
- `--fps`: Frames per second for sampling
- `--model`: Gemini model to use
- `--export/--no-export`: Export prompts to all formats (default: True)
- `--verbose, -v`: Verbose output

### `ai-video export-prompts`

Export prompts to various formats.

**Options:**
- `video_id`: Video ID to export prompts for (required)
- `--format, -f`: Export format: md, json, shot-list, or all (default: all)
- `--output, -o`: Output directory
- `--verbose, -v`: Verbose output

### `ai-video doctor`

Check environment and configuration.

**Options:**
- `--verbose, -v`: Verbose output

## Prompt Templates

The system includes comprehensive prompt templates for different generation tasks:

### Text-to-Image Prompts

Format: `Subject + Action + Scene + Camera + Lighting + Style`

Example:
```
A woman with long blonde hair wearing a white t-shirt and blue jeans, 
pouring coffee into a ceramic mug in a modern kitchen with white marble 
counters and stainless steel appliances. Medium shot, camera at eye level. 
Soft morning light streams through large windows, creating warm highlights 
and gentle shadows. Cinematic style with warm color grading, natural film 
look, peaceful morning atmosphere.
```

### Image-to-Video Prompts

Format: `Subject + Action + Background + Background Movement + Camera Movement`

Example:
```
The woman in the white t-shirt turns her head and smiles at the camera, 
her blonde hair moves gently in the breeze. Soft kitchen background 
slightly out of focus. Camera remains static at medium shot.
```

### Text-to-Video Prompts

Format: `Subject + Action + Scene + Camera Movement + Lighting + Style`

## Advanced Usage

### Custom Analysis with FPS Control

```bash
# Sample at 2 frames per second for detailed analysis
ai-video analyze --input video.mp4 --fps 2
```

### Analyze Video Segments

```bash
# Analyze only the middle portion
ai-video analyze --input video.mp4 --start 1m --end 3m
```

### Pipeline with Custom Run ID

```bash
# Use a specific run ID for organization
ai-video run-all --input video.mp4 --run-id commercial_v1
```

### Resume Failed Pipeline

The pipeline automatically creates checkpoints. If a run fails, you can check the manifest in `assets/runs/` to see what completed.

## Architecture

```
ai-video/
├── src/ai_video/
│   ├── agents/              # AI agents
│   │   ├── video_analysis.py    # Gemini-powered analysis
│   │   └── prompt_generation.py # Prompt generation
│   ├── pipeline/            # Orchestration
│   │   ├── orchestrator.py      # Pipeline management
│   │   └── export.py            # Export utilities
│   ├── prompts/             # Prompt templates
│   │   ├── gemini_video_blueprint.md
│   │   ├── image_prompt_template.md
│   │   └── video_prompt_template.md
│   ├── data/                # Constants and reference data
│   ├── models.py            # Pydantic data models
│   ├── gemini_client.py     # Gemini API wrapper
│   ├── settings.py          # Configuration
│   ├── paths.py             # Path management
│   ├── storage.py           # File I/O
│   ├── logging.py           # Logging utilities
│   ├── safety.py            # Validation
│   ├── utils.py             # Helper functions
│   └── cli.py               # CLI application
```

## Best Practices

1. **Video Length**: For best results, analyze videos under 5 minutes. For longer videos, use `--start` and `--end` to analyze segments.

2. **FPS Setting**: Default 1 FPS works well for most videos. Increase to 2-3 FPS for fast-paced action scenes.

3. **API Key**: Never commit your `.env` file. Always use environment variables for sensitive data.

4. **Model Selection**: Use `gemini-2.0-flash-exp` for speed, `gemini-2.5-pro` for highest quality analysis.

5. **YouTube Videos**: For YouTube, use the full video URL, not shortened youtu.be links.

## Troubleshooting

### "API key is required"
Make sure you have set `GOOGLE_API_KEY` in your `.env` file.

### "Video file not found"
Use absolute paths or ensure you're in the correct directory.

### "Failed to parse JSON response"
The Gemini model might have returned invalid JSON. Try running again or use a different model.

### FFmpeg not found
Install FFmpeg: `brew install ffmpeg` (macOS) or see https://ffmpeg.org/download.html

## Contributing

Contributions are welcome! Please follow the existing code style and add tests for new features.

## License

[Add your license here]

## Acknowledgments

- Built with Google Gemini 2.5 for video understanding
- Prompt templates based on best practices from leading AI video generation tools
- Inspired by the workflow described in workflow.md
