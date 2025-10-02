"""Command-line interface for AI Video."""

from pathlib import Path
from typing import Optional
import sys

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .agents.video_analysis import VideoAnalysisAgent
from .agents.prompt_generation import PromptGenerationAgent
from .agents.reimagination_agent import ReimaginationAgent
from .pipeline.orchestrator import PipelineOrchestrator
from .pipeline.export import PromptExporter
from .models import VideoReport
from .paths import path_builder
from .storage import load_model
from .settings import settings
from .safety import validate_api_key, ValidationError
from .logging import setup_logger
from .utils import format_duration
from .export import generate_detailed_markdown

app = typer.Typer(
    name="ai-video",
    help="AI-powered video analysis and prompt generation for video recreation",
    add_completion=False
)
console = Console()

@app.command()
def analyze(
    input: str = typer.Argument(..., help="Path to video file or YouTube URL"),
    video_id: Optional[str] = typer.Option(None, "--id", help="Custom video ID"),
    start: Optional[str] = typer.Option(None, "--start", help="Start offset (e.g., '10s')"),
    end: Optional[str] = typer.Option(None, "--end", help="End offset (e.g., '120s')"),
    fps: Optional[int] = typer.Option(None, "--fps", help="Frames per second for sampling"),
    model: Optional[str] = typer.Option(None, "--model", help="Gemini model to use"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Analyze a video and generate a structured report."""
    logger = setup_logger("ai_video.cli", level="DEBUG" if verbose else "INFO")
    
    try:
        console.print(f"[bold cyan]Analyzing video:[/bold cyan] {input}")
        
        agent = VideoAnalysisAgent(model=model)
        report = agent.analyze(
            video_source=input,
            video_id=video_id,
            save_report=True,
            start_offset=start,
            end_offset=end,
            fps=fps
        )
        
        report_path = path_builder.get_report_path(report.video_id)
        
        console.print(f"\n[bold green]✓ Analysis complete![/bold green]")
        console.print(f"[cyan]Video ID:[/cyan] {report.video_id}")
        console.print(f"[cyan]Duration:[/cyan] {format_duration(report.duration)}")
        console.print(f"[cyan]Scenes:[/cyan] {len(report.scenes)}")
        console.print(f"[cyan]Report saved to:[/cyan] {report_path}")
        
        if verbose and report.scenes:
            console.print("\n[bold]Scenes:[/bold]")
            for scene in report.scenes[:5]:
                console.print(f"  Scene {scene.scene_index}: {scene.location} ({scene.duration:.1f}s)")
            if len(report.scenes) > 5:
                console.print(f"  ... and {len(report.scenes) - 5} more scenes")
    
    except ValidationError as e:
        console.print(f"[bold red]✗ Validation error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)

@app.command()
def make_prompts(
    report: str = typer.Argument(..., help="Path to report JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Generate prompts from a video analysis report."""
    logger = setup_logger("ai_video.cli", level="DEBUG" if verbose else "INFO")
    
    try:
        report_path = Path(report)
        console.print(f"[bold cyan]Loading report:[/bold cyan] {report_path}")
        
        video_report = load_model(report_path, VideoReport)
        
        console.print(f"[bold cyan]Generating prompts...[/bold cyan]")
        agent = PromptGenerationAgent()
        bundles = agent.generate_prompts(video_report, save_bundles=True)
        
        # Generate detailed markdown
        prompts_dir = path_builder.get_video_prompts_dir(video_report.video_id)
        markdown_path = prompts_dir / "prompts_detailed.md"
        console.print(f"[bold cyan]Generating detailed markdown...[/bold cyan]")
        generate_detailed_markdown(video_report, markdown_path, bundles=bundles)
        
        console.print(f"\n[bold green]✓ Prompt generation complete![/bold green]")
        console.print(f"[cyan]Video ID:[/cyan] {video_report.video_id}")
        console.print(f"[cyan]Scenes processed:[/cyan] {len(bundles)}")
        console.print(f"[cyan]Prompts saved to:[/cyan] {prompts_dir}")
        console.print(f"[cyan]Detailed markdown:[/cyan] {markdown_path}")
        
        if verbose and bundles:
            console.print("\n[bold]Sample prompts:[/bold]")
            for bundle in bundles[:2]:
                console.print(f"\n  Scene {bundle.scene_index}:")
                if bundle.image_prompts:
                    console.print(f"    Image: {bundle.image_prompts[0].text[:80]}...")
                if bundle.video_prompts:
                    console.print(f"    Video: {bundle.video_prompts[0].text[:80]}...")
    
    except ValidationError as e:
        console.print(f"[bold red]✗ Validation error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)

@app.command()
def run_all(
    input: str = typer.Argument(..., help="Path to video file or YouTube URL"),
    video_id: Optional[str] = typer.Option(None, "--id", help="Custom video ID"),
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Custom run ID"),
    start: Optional[str] = typer.Option(None, "--start", help="Start offset (e.g., '10s')"),
    end: Optional[str] = typer.Option(None, "--end", help="End offset (e.g., '120s')"),
    fps: Optional[int] = typer.Option(None, "--fps", help="Frames per second for sampling"),
    model: Optional[str] = typer.Option(None, "--model", help="Gemini model to use"),
    export: bool = typer.Option(True, "--export/--no-export", help="Export prompts to all formats"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Run the complete pipeline: analyze video and generate prompts."""
    logger = setup_logger("ai_video.cli", level="DEBUG" if verbose else "INFO")
    
    try:
        console.print(f"[bold cyan]Starting pipeline for:[/bold cyan] {input}\n")
        
        orchestrator = PipelineOrchestrator(model=model)
        manifest = orchestrator.run_all(
            video_source=input,
            video_id=video_id,
            run_id=run_id,
            start_offset=start,
            end_offset=end,
            fps=fps
        )
        
        console.print(f"\n[bold green]✓ Pipeline complete![/bold green]")
        console.print(f"[cyan]Run ID:[/cyan] {manifest['run_id']}")
        console.print(f"[cyan]Video ID:[/cyan] {manifest['video_id']}")
        console.print(f"[cyan]Status:[/cyan] {manifest['status']}")
        
        if 'num_scenes' in manifest.get('artifacts', {}):
            console.print(f"[cyan]Scenes:[/cyan] {manifest['artifacts']['num_scenes']}")
        
        if manifest.get('artifacts'):
            console.print(f"\n[bold]Artifacts:[/bold]")
            for key, value in manifest['artifacts'].items():
                if key != 'prompt_bundles':
                    console.print(f"  {key}: {value}")
        
        if export and manifest['status'] == 'completed':
            console.print(f"\n[bold cyan]Exporting prompts...[/bold cyan]")
            
            report_path = Path(manifest['artifacts']['report'])
            report = load_model(report_path, VideoReport)
            
            export_paths = PromptExporter.export_all_formats(
                video_id=manifest['video_id'],
                report=report
            )
            
            # Generate detailed markdown
            prompts_dir = path_builder.get_video_prompts_dir(manifest['video_id'])
            markdown_path = prompts_dir / "prompts_detailed.md"
            console.print(f"[bold cyan]Generating detailed markdown...[/bold cyan]")
            generate_detailed_markdown(report, markdown_path)
            export_paths['detailed_markdown'] = str(markdown_path)
            
            console.print(f"[bold green]✓ Export complete![/bold green]")
            for format_name, path in export_paths.items():
                console.print(f"  {format_name}: {path}")
    
    except ValidationError as e:
        console.print(f"[bold red]✗ Validation error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)


@app.command()
def reimagine(
    input: str = typer.Option(..., "--input", "-i", help="Path to prompts_detailed.md"),
    style: Optional[str] = typer.Option(None, "--style", "-s", help="Global style directive"),
    num_variants: int = typer.Option(3, "--num-variants", "-n", help="Variants per scene (1-5)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Directory for outputs"),
    model: Optional[str] = typer.Option(None, "--model", help="Override Gemini model"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    user_prompt: Optional[str] = typer.Option(
        None,
        "--user-prompt",
        "-u",
        help="Additional free-form instructions applied to every variant",
    ),
) -> None:
    """Generate creative prompt variants for an existing prompt pack."""
    logger = setup_logger("ai_video.cli", level="DEBUG" if verbose else "INFO")

    try:
        console.print(f"[bold cyan]Reimagining prompts from:[/bold cyan] {input}")
        agent = ReimaginationAgent(model=model)
        result = agent.generate_reimagined_prompts(
            input_file=input,
            style=style,
            num_variants=num_variants,
            output_dir=output,
            user_prompt=user_prompt,
        )

        artifacts = result.get("artifacts", {})

        console.print(f"\n[bold green]✓ Reimagination complete![/bold green]")
        console.print(f"[cyan]Scenes processed:[/cyan] {result['total_scenes']}")
        console.print(f"[cyan]Variants per scene:[/cyan] {result['num_variants_per_scene']}")
        console.print(f"[cyan]Total variants:[/cyan] {result['total_variants']}")
        console.print(f"[cyan]Global style:[/cyan] {result['global_style']['name']}")
        if result.get('user_prompt'):
            console.print(f"[cyan]User prompt:[/cyan] {result['user_prompt']}")

        if artifacts:
            console.print("\n[bold]Artifacts:[/bold]")
            for key, value in artifacts.items():
                console.print(f"  {key}: {value}")

    except ValidationError as exc:
        console.print(f"[bold red]✗ Validation error:[/bold red] {exc}")
        raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"[bold red]✗ Error:[/bold red] {exc}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)

@app.command()
def export_prompts(
    video_id: str = typer.Argument(..., help="Video ID to export prompts for"),
    format: str = typer.Option("all", "--format", "-f", help="Export format: json, shot-list, or all"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Export prompts to various formats."""
    logger = setup_logger("ai_video.cli", level="DEBUG" if verbose else "INFO")
    
    try:
        console.print(f"[bold cyan]Exporting prompts for:[/bold cyan] {video_id}")
        
        if output_dir is None:
            output_dir = path_builder.get_video_prompts_dir(video_id)
        
        bundles = PromptExporter.load_bundles_from_video_id(video_id)
        
        if not bundles:
            console.print(f"[bold yellow]⚠ No prompt bundles found for video ID: {video_id}[/bold yellow]")
            raise typer.Exit(code=1)
        
        report_path = path_builder.get_report_path(video_id)
        report = load_model(report_path, VideoReport) if report_path.exists() else None
        
        exported = []
        
        if format in ["json", "all"]:
            json_path = output_dir / "prompts.json"
            PromptExporter.export_to_json(bundles, json_path, report)
            exported.append(("JSON", str(json_path)))
        
        if format in ["shot-list", "all"]:
            shot_list_path = output_dir / "shot_list.md"
            PromptExporter.export_shot_list(bundles, shot_list_path)
            exported.append(("Shot List", str(shot_list_path)))
        
        console.print(f"\n[bold green]✓ Export complete![/bold green]")
        for name, path in exported:
            console.print(f"  {name}: {path}")
    
    except ValidationError as e:
        console.print(f"[bold red]✗ Validation error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)

@app.command()
def doctor(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Check environment and configuration."""
    console.print("[bold cyan]AI Video Doctor - Environment Check[/bold cyan]\n")
    
    checks = []
    
    api_key = settings.google_api_key
    if api_key and len(api_key) > 10:
        checks.append(("Google API Key", "✓", "green"))
    else:
        checks.append(("Google API Key", "✗ Not configured", "red"))
    
    try:
        import google.genai
        checks.append(("google-genai", "✓ Installed", "green"))
    except ImportError:
        checks.append(("google-genai", "✗ Not installed", "red"))
    
    import subprocess
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            checks.append(("FFmpeg", "✓ Available", "green"))
        else:
            checks.append(("FFmpeg", "⚠ Check failed", "yellow"))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        checks.append(("FFmpeg", "✗ Not found", "yellow"))
    
    for dir_name in ["assets_dir", "reports_dir", "prompts_dir", "runs_dir", "logs_dir"]:
        dir_path = getattr(settings, dir_name)
        if dir_path.exists():
            checks.append((f"{dir_name}", f"✓ {dir_path}", "green"))
        else:
            checks.append((f"{dir_name}", f"✗ {dir_path}", "yellow"))
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    
    for name, status, color in checks:
        table.add_row(name, f"[{color}]{status}[/{color}]")
    
    console.print(table)
    
    if verbose:
        console.print(f"\n[bold]Configuration:[/bold]")
        console.print(f"  Gemini Model: {settings.gemini.model}")
        console.print(f"  Log Level: {settings.log_level}")
        console.print(f"  Assets Dir: {settings.assets_dir}")
    
    all_good = all(status == "✓" or "✓" in status for _, status, _ in checks[:2])
    
    if all_good:
        console.print(f"\n[bold green]✓ All critical checks passed![/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠ Some checks failed. Please configure your environment.[/bold yellow]")
        console.print(f"\nRun: [cyan]cp .env.example .env[/cyan] and set your GOOGLE_API_KEY")

@app.callback()
def main():
    """AI Video - Video analysis and prompt generation."""
    pass

if __name__ == "__main__":
    app()
