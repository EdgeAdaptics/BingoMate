"""Tests for the skills module."""
from __future__ import annotations

import pytest

from bingomate.skills import (
    BingoExpressionSkill,
    BingoHelpfulTipSkill,
    BingoObservationSkill,
    BingoPrivacyAcknowledgmentSkill,
    EchoSkill,
    ReminderDraftSkill,
    SkillRegistry,
    SkillResult,
    build_default_registry,
)


def test_skill_registry_init() -> None:
    """Test skill registry initialization."""
    registry = SkillRegistry()
    assert registry.names() == []


def test_skill_registry_register() -> None:
    """Test registering a skill."""
    registry = SkillRegistry()
    echo_skill = EchoSkill()
    
    registry.register(echo_skill)
    assert "echo" in registry.names()


def test_skill_registry_describe() -> None:
    """Test describing skills."""
    registry = SkillRegistry()
    registry.register(EchoSkill())
    registry.register(ReminderDraftSkill())
    
    descriptions = registry.describe()
    assert len(descriptions) >= 2
    assert any(d["name"] == "echo" for d in descriptions)
    assert any(d["name"] == "reminder_draft" for d in descriptions)


def test_skill_registry_run_echo() -> None:
    """Test running echo skill."""
    registry = SkillRegistry()
    registry.register(EchoSkill())
    
    result = registry.run("echo", "test prompt", {})
    assert result.ok is True
    assert result.data["prompt"] == "test prompt"


def test_skill_registry_run_unknown() -> None:
    """Test running unknown skill."""
    registry = SkillRegistry()
    result = registry.run("unknown_skill", "test", {})
    
    assert result.ok is False
    assert "Unknown skill" in result.message


def test_echo_skill() -> None:
    """Test echo skill directly."""
    skill = EchoSkill()
    context = {"test": "value"}
    
    result = skill.run("hello world", context)
    assert result.ok is True
    assert result.data["prompt"] == "hello world"
    assert result.data["context"] == context


def test_reminder_draft_skill() -> None:
    """Test reminder draft skill."""
    skill = ReminderDraftSkill()
    
    result = skill.run("remind me to update firmware", {})
    assert result.ok is True
    assert "approval" in result.message.lower()
    assert result.data["requires_user_approval"] is True


def test_default_registry_includes_bingo_personality_skills() -> None:
    """Test default registry includes Bingo personality skills."""
    registry = build_default_registry()
    names = registry.names()

    assert "bingo_express" in names
    assert "bingo_observe" in names
    assert "bingo_helpful_tip" in names
    assert "bingo_privacy_check" in names


def test_bingo_personality_skills() -> None:
    """Test Bingo personality skills return useful local responses."""
    expression = BingoExpressionSkill().run("success", {})
    observation = BingoObservationSkill().run("demo complete", {"achievement_type": "progress"})
    tip = BingoHelpfulTipSkill().run("validate ESP32 serial", {})
    privacy = BingoPrivacyAcknowledgmentSkill().run("execute", {})

    assert expression.ok is True
    assert "expression" in expression.data
    assert observation.ok is True
    assert "observation" in observation.data
    assert tip.ok is True
    assert "tip_prefix" in tip.data
    assert privacy.ok is True
    assert "permission_request" in privacy.data
