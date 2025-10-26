"""Tests for the Gemini client helpers."""

import itertools
from types import SimpleNamespace

import pytest

from ai_video.gemini_client import GeminiVisionClient


class _FakeFilesClient:
    """Simple stand-in for the Gemini files client."""

    def __init__(self, responses):
        self._responses = iter(responses)

    def get(self, name: str):
        try:
            return next(self._responses)
        except StopIteration:  # pragma: no cover - guard for unexpected exhaustion
            return SimpleNamespace(name=name, state="PROCESSING", error=None, uri="files/uri")


def _build_client(responses, timeout_s=1.0, poll_interval_s=0.0):
    client = GeminiVisionClient.__new__(GeminiVisionClient)
    client.client = SimpleNamespace(files=_FakeFilesClient(responses))
    client.file_activation_timeout_s = timeout_s
    client.file_activation_poll_interval_s = poll_interval_s
    return client


def test_wait_for_file_activation_returns_active():
    responses = [
        SimpleNamespace(name="files/1", state="PROCESSING", error=None, uri="files/1"),
        SimpleNamespace(name="files/1", state="ACTIVE", error=None, uri="files/1"),
    ]
    client = _build_client(responses)

    result = client._wait_for_file_activation("files/1")

    assert result.state == "ACTIVE"


def test_wait_for_file_activation_handles_enum_state():
    class _EnumStub:
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return f"FileState.{self.value}"

    responses = [
        SimpleNamespace(name="files/2", state=_EnumStub("PROCESSING"), error=None, uri="files/2"),
        SimpleNamespace(name="files/2", state=_EnumStub("ACTIVE"), error=None, uri="files/2"),
    ]
    client = _build_client(responses)

    result = client._wait_for_file_activation("files/2")

    assert isinstance(result.state, _EnumStub)
    assert result.state.value == "ACTIVE"


def test_wait_for_file_activation_raises_on_failed_state():
    responses = [
        SimpleNamespace(name="files/1", state="PROCESSING", error=None, uri="files/1"),
        SimpleNamespace(
            name="files/1",
            state="FAILED",
            error={"code": 400, "message": "File rejected"},
            uri="files/1",
        ),
    ]
    client = _build_client(responses)

    with pytest.raises(RuntimeError) as exc:
        client._wait_for_file_activation("files/1")

    assert "processing failed" in str(exc.value)


def test_wait_for_file_activation_times_out():
    infinite_processing = itertools.repeat(
        SimpleNamespace(name="files/1", state="PROCESSING", error=None, uri="files/1")
    )
    client = _build_client(infinite_processing, timeout_s=0.05, poll_interval_s=0.0)

    with pytest.raises(TimeoutError):
        client._wait_for_file_activation("files/1")
