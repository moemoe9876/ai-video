# Implementation Plan

## Project Setup
- [ ] Step 1: Initialize repo and tooling
  - **Task**: Set up Python project scaffolding, virtual environment, dependency management, and baseline folders. Establish `.env` handling for Gemini API key only.
  - **Files**:
    - `pyproject.toml`: Tooling config (optionally Black/Ruff) and project metadata.
    - `requirements.txt`: Python runtime dependencies.
    - `.env.example`: Document required environment variables.
    - `config.yaml`: Central config (models, paths, defaults).
    - `src/ai_video/__init__.py`: Package marker.
    - `src/ai_video/settings.py`: Load `.env` and `config.yaml` with sane defaults.
  - **Step Dependencies**: None
  - **User Instructions**:
    - Ensure Python 3.10+ is installed.
    - Create venv: `python -m venv venv && source venv/bin/activate`
    - Install deps: `pip install -r requirements.txt`
    - Copy env template: `cp .env.example .env` and set `GOOGLE_API_KEY`.

- [ ] Step 2: Define frameworks and system prerequisites
  - **Task**: Choose core frameworks and ensure system tools are available for video IO.
  - **Files**:
    - `docs/frameworks.md`: Rationale and versions for SDKs and libs.
  - **Step Dependencies**: Project Setup > Step 1
  - **User Instructions**:
    - Install FFmpeg (for local video probing/clipping): `brew install ffmpeg` (macOS) or your OS package manager.
    - Libraries:
      - Gemini: `google-genai`
      - CLI: `typer`, `rich`
      - Config: `pydantic`, `PyYAML`
      - Media utils (optional): `opencv-python`, `Pillow`, `numpy`
      - HTTP/Utils: `requests`, `tqdm`, `pathlib`

## Core Abstractions & Data Models
- [ ] Step 1: Define domain models
  - **Task**: Create Pydantic models for `VideoReport`, `Scene`, `Shot`, `Entity`, `PromptSpec`, and `PromptBundle`. Include serialization and validation.
  - **Files**:
    - `src/ai_video/models.py`: Core models and enums.
  - **Step Dependencies**: Project Setup > Step 1
  - **User Instructions**:
    - No action; used by agents and pipeline.

- [ ] Step 2: Asset paths and naming
  - **Task**: Centralize paths for inputs/outputs with deterministic naming (scene/shot indices). Provide helpers for manifests and JSON read/write.
  - **Files**:
    - `src/ai_video/paths.py`: Root dirs, path builders (inputs, reports, prompts, logs).
    - `src/ai_video/storage.py`: JSON read/write and atomic file ops.
  - **Step Dependencies**: Core Abstractions & Data Models > Step 1
  - **User Instructions**:
    - Configure `assets_dir` in `config.yaml` if needed.

## Gemini Provider (Only API)
- [ ] Step 1: Gemini client wrapper
  - **Task**: Implement a thin wrapper over `google.genai` for video understanding. Support: local file upload via Files API; YouTube URL ingestion; optional clipping and fps hints; request sizing (inline vs File API).
  - **Files**:
    - `src/ai_video/gemini_client.py`: `GeminiVisionClient` with helpers for analyze_video and analyze_images.
    - `src/ai_video/prompts/gemini_video_blueprint.md`: System/user prompts to extract a structured report.
  - **Step Dependencies**: Core Abstractions & Data Models > Step 1
  - **User Instructions**:
    - Set `GOOGLE_API_KEY` in `.env`.
    - Prefer File API for videos >20MB; pass YouTube URLs directly when applicable.

## Agents
- [ ] Step 1: Video Analysis Agent
  - **Task**: Ingest source video (file or YouTube) and produce a `VideoReport` capturing scenes/shots, subjects, actions, camera, lighting, style, and key timestamps. Persist `report.json` and optional thumbnails.
  - **Files**:
    - `src/ai_video/agents/video_analysis.py`: Uses `GeminiVisionClient` and optional FFmpeg/OpenCV for frame sampling.
    - `assets/reports/report.json`: Output spec for the input video.
  - **Step Dependencies**: Gemini Provider > Step 1; Core Abstractions & Data Models > Step 2
  - **User Instructions**:
    - `ai-video analyze --input path/to/video.mp4` or YouTube URL.

- [ ] Step 2: Prompt Generation Agent
  - **Task**: Convert the `VideoReport` into structured prompts following best practices (Subject + Action + Scene + Camera + Lighting + Style). Emit both image prompts (for T2I tools) and video prompts (for I2V/T2V tools) without calling those tools.
  - **Files**:
    - `src/ai_video/agents/prompt_generation.py`: Renders prompt templates per scene/shot.
    - `src/ai_video/data/constants.py`: Lighting modes and color film types from `light-color-camera.md`.
    - `src/ai_video/prompts/image_prompt_template.md`: Template for image prompts.
    - `src/ai_video/prompts/video_prompt_template.md`: Template for video prompts.
    - `assets/prompts/scene_{idx}.json`: Emitted prompt bundles per scene.
  - **Step Dependencies**: Agents > Step 1
  - **User Instructions**:
    - `ai-video make-prompts --report assets/reports/report.json`

## Orchestration & Pipeline
- [ ] Step 1: Prompt-only pipeline runner
  - **Task**: Implement an orchestrator that runs analyze → make-prompts with checkpoints, retries, and resumability. Save a run manifest.
  - **Files**:
    - `src/ai_video/pipeline/orchestrator.py`: High‑level `run_all()` for prompt-only flow.
    - `assets/runs/run_{timestamp}.json`: Manifest of artifacts and settings.
  - **Step Dependencies**: Agents > Steps 1–2; Core Abstractions & Data Models > Step 2
  - **User Instructions**:
    - `ai-video run-all --input path/to/video.mp4 --out assets/runs/latest`

- [ ] Step 2: Export formats
  - **Task**: Export consolidated prompts as Markdown and JSON for downstream tools. Include a compact “shot list” and a verbose “director’s notes” variant.
  - **Files**:
    - `src/ai_video/pipeline/export.py`: Builders for `prompts.md` and `prompts.json` from prompt bundles.
    - `assets/prompts/prompts.md`: Human-readable output.
  - **Step Dependencies**: Orchestration & Pipeline > Step 1
  - **User Instructions**:
    - `ai-video export --prompts-dir assets/prompts --format md`

## CLI
- [ ] Step 1: Command-line interface
  - **Task**: Provide `ai-video` CLI with subcommands: `analyze`, `make-prompts`, `run-all`, `export`, and `doctor` (env check). Add progress, logging, and dry‑run.
  - **Files**:
    - `src/ai_video/cli.py`: Typer app and command wiring.
    - `scripts/ai-video`: Entry point shim.
  - **Step Dependencies**: Orchestration & Pipeline > Step 1; Agents implemented
  - **User Instructions**:
    - `python -m ai_video --help` or install console script via `pyproject.toml`.

## Observability & Safety
- [ ] Step 1: Logging and telemetry
  - **Task**: Structured logging (JSON), request/response redaction for secrets, artifact indexing, and basic metrics.
  - **Files**:
    - `src/ai_video/logging.py`: Logger setup and context helpers.
    - `assets/logs/…`: Runtime logs.
  - **Step Dependencies**: Project Setup > Step 1
  - **User Instructions**:
    - Configure log level via `LOG_LEVEL` env var.

- [ ] Step 2: Safety and guardrails
  - **Task**: Add validators, file size checks, and Gemini request sizing logic (inline vs File API). Support YouTube URL validation and optional clipping to reduce tokens.
  - **Files**:
    - `src/ai_video/safety.py`: Validation utilities.
    - `src/ai_video/utils.py`: Request sizing and file upload helpers.
  - **Step Dependencies**: Gemini Provider > Step 1; Core Abstractions & Data Models > Step 2
  - **User Instructions**:
    - Use `--dry-run` to preview work without API calls.





## Repository Layout (Proposed)

```text
./
├─ IMPLEMENTATION_PLAN.md
├─ gemini.md
├─ how-to-prompt.md
├─ light-color-camera.md
├─ workflow.md
├─ config.yaml
├─ requirements.txt
├─ pyproject.toml
├─ .env.example
├─ assets/
│  ├─ inputs/
│  ├─ reports/
│  ├─ prompts/
│  ├─ runs/
│  └─ logs/
├─ src/
│  └─ ai_video/
│     ├─ __init__.py
│     ├─ settings.py
│     ├─ models.py
│     ├─ paths.py
│     ├─ storage.py
│     ├─ logging.py
│     ├─ safety.py
│     ├─ utils.py
│     ├─ cli.py
│     ├─ data/
│     │  └─ constants.py
│     ├─ prompts/
│     │  ├─ gemini_video_blueprint.md
│     │  ├─ image_prompt_template.md
│     │  └─ video_prompt_template.md
│     ├─ gemini_client.py
│     ├─ agents/
│     │  ├─ video_analysis.py
│     │  └─ prompt_generation.py
│     └─ pipeline/
│        ├─ orchestrator.py
│        └─ export.py
├─ scripts/
│  └─ ai-video
```

## Configuration Keys (Example)
- `GOOGLE_API_KEY`: Gemini API key
- `ASSETS_DIR`: Root output directory (default `assets/`)
- `MODEL_GEMINI`: e.g., `gemini-2.5-pro` or `gemini-2.5-flash`

## Prompting Guidance (Built-in)
- Prompts follow structures from `how-to-prompt.md`:
  - Text→Video: Subject + Action + Scene + (Camera + Lighting + Style)
  - Image→Video: Subject + Action + Background + Background Movement + Camera
- Use transition markers like “switch to …” between shots.
- Prefer realistic physics for motion; avoid strict numbers.
- Leverage lighting/film vocab from `light-color-camera.md` for look matching.

## Gemini Vision Notes
- For large media, use File API; for YouTube, pass `file_uri` directly.
- Consider clipping long videos or lowering FPS sampling to control tokens.
- When extracting structure, request JSON with clear schemas (scenes, shots, entities).

## Validation Checklist
- Can analyze a video and produce a structured `VideoReport`.
- Generates per‑scene prompt bundles (image + video variants).
- Exports consolidated prompts to Markdown and JSON.
- All artifacts are discoverable via run manifests.

## Quickstart (Once Implemented)
- Analyze: `ai-video analyze --input assets/inputs/sample.mp4`
- Prompts: `ai-video make-prompts --report assets/reports/report.json`
- Export: `ai-video export --prompts-dir assets/prompts --format md`

