"""Pipeline orchestrator for running the full analysis and prompt generation flow."""

from pathlib import Path
from typing import Union, Optional, Dict, Any
from datetime import datetime
import json

from ..agents.video_analysis import VideoAnalysisAgent
from ..agents.prompt_generation import PromptGenerationAgent
from ..models import VideoReport
from ..paths import path_builder
from ..storage import write_json
from ..utils import get_run_id
from ..logging import get_logger, LogContext
from ..settings import settings

logger = get_logger(__name__)

class PipelineOrchestrator:
    """Orchestrates the full video analysis and prompt generation pipeline."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.analysis_agent = VideoAnalysisAgent(api_key=api_key, model=model)
        self.prompt_agent = PromptGenerationAgent()
        self.config = settings.pipeline
    
    def run_all(
        self,
        video_source: Union[str, Path],
        video_id: Optional[str] = None,
        run_id: Optional[str] = None,
        start_offset: Optional[str] = None,
        end_offset: Optional[str] = None,
        fps: Optional[int] = None,
        skip_analysis: bool = False,
        skip_prompts: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline: analyze video and generate prompts.
        
        Args:
            video_source: Path to video or YouTube URL
            video_id: Optional video ID
            run_id: Optional run ID
            start_offset: Optional start time offset
            end_offset: Optional end time offset
            fps: Optional FPS for sampling
            skip_analysis: Skip video analysis (use existing report)
            skip_prompts: Skip prompt generation
        
        Returns:
            Manifest dictionary with paths and metadata
        """
        if run_id is None:
            run_id = get_run_id()
        
        with LogContext(logger, f"Pipeline run: {run_id}"):
            manifest = {
                "run_id": run_id,
                "video_source": str(video_source),
                "video_id": video_id,
                "started_at": datetime.now().isoformat(),
                "config": {
                    "start_offset": start_offset,
                    "end_offset": end_offset,
                    "fps": fps,
                    "skip_analysis": skip_analysis,
                    "skip_prompts": skip_prompts,
                },
                "artifacts": {},
                "status": "running",
                "errors": []
            }
            
            try:
                if not skip_analysis:
                    report = self._run_analysis(
                        video_source, video_id, start_offset, end_offset, fps
                    )
                    manifest["video_id"] = report.video_id
                    manifest["artifacts"]["report"] = str(
                        path_builder.get_report_path(report.video_id)
                    )
                else:
                    if video_id is None:
                        raise ValueError("video_id required when skip_analysis=True")
                    report_path = path_builder.get_report_path(video_id)
                    report = PromptGenerationAgent.load_report(report_path)
                    manifest["video_id"] = video_id
                    manifest["artifacts"]["report"] = str(report_path)
                
                if not skip_prompts:
                    bundles = self._run_prompt_generation(report)
                    manifest["artifacts"]["prompt_bundles"] = [
                        str(path_builder.get_scene_prompt_path(report.video_id, b.scene_index))
                        for b in bundles
                    ]
                    manifest["artifacts"]["num_scenes"] = len(bundles)
                
                manifest["status"] = "completed"
                manifest["completed_at"] = datetime.now().isoformat()
                
            except Exception as e:
                logger.error(f"Pipeline failed: {e}", exc_info=True)
                manifest["status"] = "failed"
                manifest["errors"].append(str(e))
                manifest["failed_at"] = datetime.now().isoformat()
                raise
            
            finally:
                manifest_path = path_builder.get_run_manifest_path(run_id)
                write_json(manifest, manifest_path)
                logger.info(f"Manifest saved: {manifest_path}")
            
            return manifest
    
    def _run_analysis(
        self,
        video_source: Union[str, Path],
        video_id: Optional[str],
        start_offset: Optional[str],
        end_offset: Optional[str],
        fps: Optional[int]
    ) -> VideoReport:
        """Run video analysis step."""
        logger.info("Step 1: Analyzing video...")
        
        attempt = 0
        last_error = None
        
        while attempt < self.config.max_retries:
            try:
                report = self.analysis_agent.analyze(
                    video_source=video_source,
                    video_id=video_id,
                    save_report=True,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    fps=fps
                )
                logger.info(f"Analysis completed: {len(report.scenes)} scenes found")
                return report
            
            except Exception as e:
                attempt += 1
                last_error = e
                logger.warning(f"Analysis attempt {attempt} failed: {e}")
                
                if not self.config.retry_on_failure or attempt >= self.config.max_retries:
                    break
        
        raise RuntimeError(f"Analysis failed after {attempt} attempts: {last_error}")
    
    def _run_prompt_generation(self, report: VideoReport):
        """Run prompt generation step."""
        logger.info("Step 2: Generating prompts...")
        
        bundles = self.prompt_agent.generate_prompts(report, save_bundles=True)
        
        logger.info(f"Prompt generation completed: {len(bundles)} bundles created")
        return bundles
    
    def resume_run(self, run_id: str) -> Dict[str, Any]:
        """Resume a failed or interrupted run."""
        logger.info(f"Resuming run: {run_id}")
        
        manifest_path = path_builder.get_run_manifest_path(run_id)
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        if manifest["status"] == "completed":
            logger.info("Run already completed")
            return manifest
        
        video_source = manifest["video_source"]
        video_id = manifest.get("video_id")
        config = manifest["config"]
        
        skip_analysis = "report" in manifest.get("artifacts", {})
        skip_prompts = "prompt_bundles" in manifest.get("artifacts", {})
        
        return self.run_all(
            video_source=video_source,
            video_id=video_id,
            run_id=run_id,
            start_offset=config.get("start_offset"),
            end_offset=config.get("end_offset"),
            fps=config.get("fps"),
            skip_analysis=skip_analysis,
            skip_prompts=skip_prompts
        )
