"""Tests for scene and shot timing normalization in the analysis agent."""

from typing import List

import pytest

from ai_video.agents.video_analysis import VideoAnalysisAgent
from ai_video.models import Scene, Shot


def _build_scene(
    scene_index: int,
    start_time: float,
    duration: float,
    shot_durations: List[float] | None = None,
) -> Scene:
    end_time = start_time + duration
    shots: List[Shot] = []

    if shot_durations:
        shot_start = start_time
        for idx, shot_duration in enumerate(shot_durations, start=1):
            shot_end = shot_start + shot_duration
            shots.append(
                Shot(
                    shot_index=idx,
                    start_time=shot_start,
                    end_time=shot_end,
                    duration=shot_duration,
                    description=f"Shot {idx}",
                    action="Action",
                )
            )
            shot_start = shot_end

    return Scene(
        scene_index=scene_index,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        location="Test location",
        description=f"Scene {scene_index}",
        shots=shots,
    )


def test_normalize_scene_timings_scales_to_full_duration():
    scenes = [
        _build_scene(1, 0.0, 10.0),
        _build_scene(2, 10.0, 8.0),
        _build_scene(3, 18.0, 9.8),
    ]

    normalized = VideoAnalysisAgent._normalize_scene_timings(scenes, video_duration=90.0)

    assert normalized[0].start_time == pytest.approx(0.0, abs=1e-3)
    assert normalized[-1].end_time == pytest.approx(90.0, abs=1e-3)
    assert sum(scene.duration for scene in normalized) == pytest.approx(90.0, abs=1e-3)
    for idx in range(len(normalized) - 1):
        assert normalized[idx].end_time == pytest.approx(normalized[idx + 1].start_time, abs=1e-3)


def test_normalize_scene_timings_preserves_relative_durations():
    scenes = [
        _build_scene(1, 0.0, 5.0),
        _build_scene(2, 5.0, 15.0),
    ]

    normalized = VideoAnalysisAgent._normalize_scene_timings(scenes, video_duration=40.0)

    ratio = normalized[0].duration / normalized[1].duration
    assert ratio == pytest.approx(5.0 / 15.0, rel=1e-3)


def test_normalize_scene_timings_updates_shots_within_scenes():
    scenes = [
        _build_scene(1, 0.0, 6.0, shot_durations=[2.0, 2.0, 2.0]),
        _build_scene(2, 6.0, 3.0, shot_durations=[1.5, 1.5]),
    ]

    normalized = VideoAnalysisAgent._normalize_scene_timings(scenes, video_duration=45.0)

    # Scene boundaries cover entire runtime
    assert normalized[-1].end_time == pytest.approx(45.0, abs=1e-3)

    # Shots span entire scene without gaps and the last shot matches scene end
    for scene in normalized:
        if scene.shots:
            assert scene.shots[0].start_time == pytest.approx(scene.start_time, abs=1e-3)
            assert scene.shots[-1].end_time == pytest.approx(scene.end_time, abs=1e-3)
            assert sum(shot.duration for shot in scene.shots) == pytest.approx(scene.duration, abs=1e-3)
