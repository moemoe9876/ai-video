"""Gemini API client wrapper for video understanding."""

from pathlib import Path
from typing import Optional, Union
import json
from google import genai
from google.genai import types

from .settings import settings
from .safety import (
    validate_video_file,
    validate_youtube_url,
    validate_api_key,
    check_file_size_for_inline
)
from .logging import get_logger
from .storage import read_text

logger = get_logger(__name__)

class GeminiVisionClient:
    """Client for Gemini vision and video understanding."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.google_api_key
        validate_api_key(self.api_key)
        
        self.model = model or settings.gemini.model
        self.client = genai.Client(api_key=self.api_key)
        self.max_retries = settings.gemini.max_retries
        
        logger.info(f"Initialized Gemini client with model: {self.model}")
    
    def analyze_video(
        self,
        video_source: Union[str, Path],
        prompt: Optional[str] = None,
        use_blueprint: bool = True,
        start_offset: Optional[str] = None,
        end_offset: Optional[str] = None,
        fps: Optional[int] = None,
        response_format: str = "json"
    ) -> dict:
        """
        Analyze a video and extract structured information.
        
        Args:
            video_source: Path to video file or YouTube URL
            prompt: Custom prompt (if not using blueprint)
            use_blueprint: Whether to use the video analysis blueprint
            start_offset: Start time offset (e.g., "10s")
            end_offset: End time offset (e.g., "120s")
            fps: Frames per second for sampling
            response_format: Expected response format ("json" or "text")
        
        Returns:
            Parsed response dictionary
        """
        logger.info(f"Analyzing video: {video_source}")
        
        if isinstance(video_source, str) and video_source.startswith('http'):
            if not validate_youtube_url(video_source):
                raise ValueError(f"Invalid YouTube URL: {video_source}")
            return self._analyze_youtube_video(
                video_source, prompt, use_blueprint, 
                start_offset, end_offset, fps, response_format
            )
        else:
            video_path = Path(video_source)
            validate_video_file(video_path)
            
            if check_file_size_for_inline(video_path, settings.gemini.file_api_threshold_mb):
                return self._analyze_video_inline(
                    video_path, prompt, use_blueprint,
                    start_offset, end_offset, fps, response_format
                )
            else:
                return self._analyze_video_with_file_api(
                    video_path, prompt, use_blueprint,
                    start_offset, end_offset, fps, response_format
                )
    
    def _analyze_youtube_video(
        self,
        url: str,
        prompt: Optional[str],
        use_blueprint: bool,
        start_offset: Optional[str],
        end_offset: Optional[str],
        fps: Optional[int],
        response_format: str
    ) -> dict:
        """Analyze a YouTube video."""
        logger.info(f"Analyzing YouTube video: {url}")
        
        analysis_prompt = self._get_analysis_prompt(prompt, use_blueprint)
        
        video_metadata = {}
        if start_offset:
            video_metadata['start_offset'] = start_offset
        if end_offset:
            video_metadata['end_offset'] = end_offset
        if fps:
            video_metadata['fps'] = fps
        
        parts = [
            types.Part(
                file_data=types.FileData(file_uri=url),
                video_metadata=types.VideoMetadata(**video_metadata) if video_metadata else None
            ),
            types.Part(text=analysis_prompt)
        ]
        
        config = None
        if response_format == "json":
            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=types.Content(parts=parts),
            config=config
        )
        
        return self._parse_response(response, response_format)
    
    def _analyze_video_inline(
        self,
        video_path: Path,
        prompt: Optional[str],
        use_blueprint: bool,
        start_offset: Optional[str],
        end_offset: Optional[str],
        fps: Optional[int],
        response_format: str
    ) -> dict:
        """Analyze video using inline data."""
        logger.info(f"Analyzing video inline: {video_path}")
        
        analysis_prompt = self._get_analysis_prompt(prompt, use_blueprint)
        
        with open(video_path, 'rb') as f:
            video_bytes = f.read()
        
        mime_type = self._get_mime_type(video_path)
        
        video_metadata = {}
        if start_offset:
            video_metadata['start_offset'] = start_offset
        if end_offset:
            video_metadata['end_offset'] = end_offset
        if fps:
            video_metadata['fps'] = fps
        
        parts = [
            types.Part(
                inline_data=types.Blob(data=video_bytes, mime_type=mime_type),
                video_metadata=types.VideoMetadata(**video_metadata) if video_metadata else None
            ),
            types.Part(text=analysis_prompt)
        ]
        
        config = None
        if response_format == "json":
            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=types.Content(parts=parts),
            config=config
        )
        
        return self._parse_response(response, response_format)
    
    def _analyze_video_with_file_api(
        self,
        video_path: Path,
        prompt: Optional[str],
        use_blueprint: bool,
        start_offset: Optional[str],
        end_offset: Optional[str],
        fps: Optional[int],
        response_format: str
    ) -> dict:
        """Analyze video using File API."""
        logger.info(f"Uploading video to File API: {video_path}")
        
        uploaded_file = self.client.files.upload(file=str(video_path))
        logger.info(f"File uploaded: {uploaded_file.name}")
        
        analysis_prompt = self._get_analysis_prompt(prompt, use_blueprint)
        
        video_metadata = {}
        if start_offset:
            video_metadata['start_offset'] = start_offset
        if end_offset:
            video_metadata['end_offset'] = end_offset
        if fps:
            video_metadata['fps'] = fps
        
        parts = [
            types.Part(
                file_data=types.FileData(file_uri=uploaded_file.uri),
                video_metadata=types.VideoMetadata(**video_metadata) if video_metadata else None
            ) if video_metadata else uploaded_file,
            types.Part(text=analysis_prompt)
        ]
        
        config = None
        if response_format == "json":
            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=parts,
            config=config
        )
        
        return self._parse_response(response, response_format)
    
    def _get_analysis_prompt(self, custom_prompt: Optional[str], use_blueprint: bool) -> str:
        """Get the analysis prompt."""
        if custom_prompt:
            return custom_prompt
        
        if use_blueprint:
            blueprint_path = Path(__file__).parent / "prompts" / "gemini_video_blueprint.md"
            return read_text(blueprint_path)
        
        return "Analyze this video in detail and provide a structured breakdown of scenes and shots."
    
    def _parse_response(self, response, response_format: str) -> dict:
        """Parse the API response."""
        text = response.text
        
        if response_format == "json":
            try:
                if text.startswith("```json"):
                    lines = text.split('\n')
                    text = '\n'.join(lines[1:-1])
                elif text.startswith("```"):
                    lines = text.split('\n')
                    text = '\n'.join(lines[1:-1])
                
                return json.loads(text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response text: {text}")
                return {"error": "Failed to parse JSON", "raw_text": text}
        
        return {"text": text}
    
    def _get_mime_type(self, video_path: Path) -> str:
        """Get MIME type for video file."""
        ext = video_path.suffix.lower().lstrip('.')
        mime_types = {
            'mp4': 'video/mp4',
            'mpeg': 'video/mpeg',
            'mpg': 'video/mpg',
            'mov': 'video/mov',
            'avi': 'video/avi',
            'webm': 'video/webm',
            'flv': 'video/x-flv',
            'wmv': 'video/wmv',
            '3gpp': 'video/3gpp',
        }
        return mime_types.get(ext, 'video/mp4')
    
    def analyze_images(
        self,
        images: list[Union[str, Path]],
        prompt: str,
        response_format: str = "text"
    ) -> dict:
        """
        Analyze multiple images.
        
        Args:
            images: List of image paths or URLs
            prompt: Analysis prompt
            response_format: Expected response format
        
        Returns:
            Parsed response
        """
        parts = []
        
        for img in images:
            if isinstance(img, str) and img.startswith('http'):
                import requests
                img_bytes = requests.get(img).content
                parts.append(types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'))
            else:
                img_path = Path(img)
                with open(img_path, 'rb') as f:
                    img_bytes = f.read()
                mime_type = f"image/{img_path.suffix.lstrip('.').lower()}"
                parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))
        
        parts.append(types.Part(text=prompt))
        
        config = None
        if response_format == "json":
            config = types.GenerateContentConfig(response_mime_type="application/json")
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=parts,
            config=config
        )
        
        return self._parse_response(response, response_format)
