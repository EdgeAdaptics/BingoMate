"""Tests for the voice pipeline module."""
from __future__ import annotations

import pytest

from bingomate.voice import VoicePipeline


def test_voice_pipeline_init() -> None:
    """Test voice pipeline initialization."""
    pipeline = VoicePipeline(
        wake_word="hey bingo",
        stt_enabled=False,
    )
    assert pipeline.wake_word == "hey bingo"
    assert pipeline.stt_configured is False


def test_voice_pipeline_stt_status() -> None:
    """Test STT status."""
    pipeline = VoicePipeline(stt_enabled=False)
    status = pipeline.stt_status()
    
    assert status["schema"] == "bingomate-stt-status/v1"
    assert status["enabled"] is False
    assert status["configured"] is False
    assert "hey bingo" in status["wake_word"]


def test_voice_pipeline_simulate_transcript() -> None:
    """Test simulated transcript."""
    pipeline = VoicePipeline(wake_word="hey bingo")
    transcript = pipeline.simulate_transcript("hey bingo summarize my lab")
    
    assert transcript["wake_detected"] is True
    assert transcript["wake_word_detected"] is True
    assert transcript["mode"] == "local-simulation"
    assert len(transcript["text"]) > 0


def test_voice_pipeline_simulate_transcript_no_wake_word() -> None:
    """Test simulated transcript without wake word."""
    pipeline = VoicePipeline(wake_word="hey bingo")
    transcript = pipeline.simulate_transcript("what time is it")
    
    assert transcript["wake_detected"] is False
    assert transcript["wake_word_detected"] is False


def test_voice_pipeline_startup_phrase() -> None:
    """Test startup phrase generation."""
    pipeline = VoicePipeline()
    phrase = pipeline.startup_phrase("Bingo")
    
    assert "Bingo" in phrase
    assert len(phrase) > 0


def test_voice_pipeline_synthesize_speech() -> None:
    """Test speech synthesis."""
    pipeline = VoicePipeline()
    synthesis = pipeline.synthesize_speech("Hello, I am Bingo")
    
    assert synthesis is not None
    assert len(synthesis.wav) > 0
    assert "local" in synthesis.mode
    assert synthesis.text == "Hello, I am Bingo"
    assert synthesis.sample_rate > 0
