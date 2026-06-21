"""Tests for the identity engine module."""
from __future__ import annotations

from pathlib import Path

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


def test_identity_system_metrics_ignores_unstable_sysfs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test thermal sysfs read errors do not break identity snapshots."""
    engine = IdentityEngine(assistant_name="Bingo")
    thermal_root = Path("/sys/devices/virtual/thermal")
    original_exists = Path.exists
    original_glob = Path.glob

    class FakeParent:
        name = "thermal_zone_test"

    class FakeTempPath:
        parent = FakeParent()

        def read_text(self, encoding: str = "utf-8") -> str:
            raise TypeError("unstable sysfs read")

    def fake_exists(path: Path) -> bool:
        if path == thermal_root:
            return True
        return original_exists(path)

    def fake_glob(path: Path, pattern: str):
        if path == thermal_root and pattern == "thermal_zone*/temp":
            return [FakeTempPath()]
        return original_glob(path, pattern)

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(Path, "glob", fake_glob)

    metrics = engine._system_metrics()

    assert metrics["temperature_c"] is None
    assert metrics["temperature_source"] == ""
