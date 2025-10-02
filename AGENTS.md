# Repository Guidelines

## Overview & Capabilities
- AI-powered video analysis and prompt generation to recreate videos with generative models.
- Accepts local files or YouTube URLs; segments scenes/shots; captures camera, lighting, subjects, and spatial relationships; exports JSON reports and human-readable prompt packs.
- Run end-to-end with `ai-video run-all` or individual steps (`analyze`, `make-prompts`, `export-prompts`).

## Tech Stack
- Python 3.10+, Typer CLI, Pydantic models, Rich/TQDM, YAML config.
- Media: OpenCV, Pillow, NumPy; system FFmpeg recommended for robust video handling.
- AI: Google Gemini via `google-genai`.
- Tooling: setuptools, Black, Ruff, Pytest; `python-dotenv` for secrets.

## Project Structure & Module Organization
- Source: `src/ai_video` → `agents/`, `pipeline/`, `prompts/`, `data/`, `cli.py`, plus `models.py`, `settings.py`, `paths.py`, `storage.py`, `logging.py`.
- Assets: `assets/inputs/`, `assets/reports/`, `assets/prompts/{video_id}/`, `assets/runs/`, `assets/logs/`. Config: `config.yaml`; env: `.env` from `.env.example`.

## Build, Test, and Development
- Setup: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && pip install -e .`
- Run: `ai-video doctor`, `ai-video analyze --input assets/inputs/sample.mp4`
- Lint/format: `ruff check .` (`--fix`), `black .` (100 cols)
- Tests: `pytest -q`

## Coding Style & Naming
- Use type hints; Pydantic for data.
- snake_case functions/modules, PascalCase classes, UPPER_CASE constants.
- No prints in library code; use `ai_video.logging`.
- Place new agents in `src/ai_video/agents/`; pipeline steps in `src/ai_video/pipeline/`.

## Testing Guidelines
- Pytest; files `tests/test_*.py` mirroring package.
- For CLI, use Typer’s `CliRunner`.
- Cover parsing, file I/O, API client logic; keep sample inputs in `assets/inputs/`.

## Commit & PR Guidelines
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:` with optional scopes (e.g., `feat(blueprint): ...`).
- PRs: summary, linked issues, sample outputs (paths under `assets/`), and test plan. Keep diffs focused.

## Security & Configuration
- Never commit secrets; keep `.env` local. Validate env with `ai-video doctor`. Defaults live in `config.yaml`. Large inputs go in `assets/inputs/`; outputs are written under `assets/`.

## Agent-Specific Notes
- When adding agents or pipeline steps, integrate via `pipeline/orchestrator.py`, align templates in `src/ai_video/prompts/`, and document flags/outputs in `README.md`.
