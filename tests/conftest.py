"""Pytest configuration for ai_video tests."""

import sys
from pathlib import Path
import types as pytypes


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))


try:
    import google.genai  # type: ignore # noqa: F401
except ImportError:
    stub_types = pytypes.ModuleType("google.genai.types")

    class _Stub:  # noqa: D401 - lightweight placeholder for optional dependency
        """Placeholder type used for stubbing google.genai types."""

        def __init__(self, *args, **kwargs):
            pass

    for attr in (
        "Part",
        "FileData",
        "VideoMetadata",
        "GenerateContentConfig",
        "Content",
        "File",
        "Blob",
    ):
        setattr(stub_types, attr, _Stub)

    stub_genai = pytypes.ModuleType("google.genai")

    class _StubClient:
        def __init__(self, *args, **kwargs):
            self.files = pytypes.SimpleNamespace(upload=None, get=None)
            self.models = pytypes.SimpleNamespace(generate_content=None)

    stub_genai.Client = _StubClient
    stub_genai.types = stub_types

    google_module = sys.modules.get("google")
    if google_module is None:
        google_module = pytypes.ModuleType("google")
        sys.modules["google"] = google_module

    setattr(google_module, "genai", stub_genai)
    sys.modules["google.genai"] = stub_genai
    sys.modules["google.genai.types"] = stub_types
