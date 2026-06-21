"""Tests for the vision pipeline module."""
from __future__ import annotations

import pytest

from bingomate.vision import VisionPipeline


def test_vision_pipeline_init() -> None:
    """Test vision pipeline initialization."""
    pipeline = VisionPipeline(camera_enabled=False, camera_index=0)
    assert pipeline.camera_enabled is False
    assert pipeline.camera_index == 0


def test_vision_pipeline_status() -> None:
    """Test vision pipeline status."""
    pipeline = VisionPipeline(camera_enabled=False)
    status = pipeline.status()
    
    assert status["schema"] == "bingomate-vision-status/v1"
    assert status["camera_enabled"] is False
    assert status["privacy"] == "camera_disabled_until_user_allows"


def test_vision_pipeline_simulate_scene() -> None:
    """Test simulated scene analysis."""
    pipeline = VisionPipeline()
    observation = pipeline.simulate_scene(label="desk")
    
    assert observation["schema"] == "bingomate-vision-observation/v1"
    assert observation["mode"] == "local-simulation"
    assert observation["scene"] == "desk"
    assert len(observation["objects"]) > 0
    assert len(observation["detections"]) > 0


def test_vision_pipeline_simulate_different_scenes() -> None:
    """Test different scene simulations."""
    pipeline = VisionPipeline()
    
    for scene in ["desk", "lab", "workshop", "home"]:
        observation = pipeline.simulate_scene(label=scene)
        assert observation["scene"] == scene
        assert observation["privacy"] == "local_only"


def test_vision_pipeline_analyze_empty_image() -> None:
    """Test analyzing empty image bytes."""
    pipeline = VisionPipeline()
    result = pipeline.analyze_image_bytes(b"", source="test")
    
    assert result is not None
    assert "empty_image" in result.get("reason", "")


def test_vision_pipeline_status_privacy() -> None:
    """Test privacy status in vision pipeline."""
    pipeline = VisionPipeline(camera_enabled=False)
    status = pipeline.status()
    
    assert status["stores_frames_by_default"] is False
    assert "disabled" in status["privacy"] or "allowed" in status["privacy"]
