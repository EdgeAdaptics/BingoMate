"""Tests for the identity engine module."""
from __future__ import annotations

import pytest

from bingomate.core import BingoMateSettings
from bingomate.identity import IdentityEngine


def test_identity_engine_init() -> None:
    """Test identity engine initialization."""
    engine = IdentityEngine(assistant_name="Bingo")
    assert engine.assistant_name == "Bingo"


def test_identity_engine_snapshot() -> None:
    """Test identity snapshot generation."""
    engine = IdentityEngine(assistant_name="Bingo")
    settings = BingoMateSettings(assistant_name="Bingo")
    
    snapshot = engine.snapshot(
        settings=settings,
        devices=[],
        skills=[],
        memories=[],
        auth_required=False,
        memory_encryption=False,
    )
    
    assert snapshot is not None
    assert "Bingo" in snapshot.get("name", "")


def test_identity_engine_system_prompt() -> None:
    """Test system prompt generation."""
    engine = IdentityEngine(assistant_name="Bingo")
    settings = BingoMateSettings(assistant_name="Bingo")
    
    snapshot = engine.snapshot(
        settings=settings,
        devices=[],
        skills=[],
        memories=[],
        auth_required=False,
        memory_encryption=False,
    )
    
    prompt = engine.system_prompt_frame(snapshot)
    assert prompt is not None
    assert len(prompt) > 0
    assert "Bingo" in prompt or "assistant" in prompt.lower()
