"""Tests for the reasoning engine module."""
from __future__ import annotations

import pytest

from bingomate.reasoning import ReasoningEngine


def test_reasoning_engine_init() -> None:
    """Test reasoning engine initialization."""
    engine = ReasoningEngine(cloud_assist=False, local_llm_enabled=False)
    assert engine.cloud_assist is False
    assert engine.local_llm.configured is False


def test_reasoning_engine_status() -> None:
    """Test reasoning engine status."""
    engine = ReasoningEngine(cloud_assist=False, local_llm_enabled=False)
    status = engine.status()
    
    assert status["schema"] == "bingomate-reasoning-status/v1"
    assert status["default_mode"] == "local-simulation"
    assert "local_llm" in status
    assert "cloud_assist" in status
    assert "deterministic_fallback" in status


def test_reasoning_engine_respond_fallback() -> None:
    """Test fallback reasoning response."""
    engine = ReasoningEngine(cloud_assist=False, local_llm_enabled=False)
    response = engine.respond("What is Jetson?")
    
    assert response is not None
    assert response["mode"] == "local-simulation"
    assert "I am Bingo" in response["response"]
    assert response["requires_cloud"] is False


def test_reasoning_engine_with_memories() -> None:
    """Test reasoning with memories."""
    engine = ReasoningEngine(cloud_assist=False, local_llm_enabled=False)
    memories = ["Jetson is an edge device", "Privacy is important"]
    
    response = engine.respond("What do you know about privacy?", memories=memories)
    
    assert response is not None
    assert "local-simulation" in response["mode"]
    assert len(memories) == 2


def test_reasoning_engine_with_identity() -> None:
    """Test reasoning with identity frame."""
    engine = ReasoningEngine(cloud_assist=False, local_llm_enabled=False)
    identity = "You are Bingo, an AI companion for edge computing."
    
    response = engine.respond("Introduce yourself", identity_frame=identity)
    
    assert response is not None
    assert response["mode"] == "local-simulation"
