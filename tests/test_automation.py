"""Tests for the automation module."""
from __future__ import annotations

import pytest

from bingomate.automation import AutomationEngine, AutomationPolicy


def test_automation_engine_propose() -> None:
    """Test automation engine propose method."""
    engine = AutomationEngine()
    proposal = engine.propose("device_online", "send_notification")
    
    assert proposal["trigger"] == "device_online"
    assert proposal["action"] == "send_notification"
    assert proposal["status"] == "proposed"
    assert proposal["requires_user_approval"] is True


def test_automation_engine_create_policy() -> None:
    """Test creating an automation policy."""
    engine = AutomationEngine()
    policy = engine.create_policy(
        "policy-1",
        "device_online",
        "log_event",
        metadata={"test": True},
    )
    
    assert policy.id == "policy-1"
    assert policy.trigger == "device_online"
    assert policy.action == "log_event"
    assert policy.enabled is False
    assert policy.approved is False


def test_automation_engine_approve_policy() -> None:
    """Test approving a policy."""
    engine = AutomationEngine()
    engine.create_policy("policy-1", "trigger", "action")
    
    success = engine.approve_policy("policy-1")
    assert success is True
    
    policy = engine.get_policy("policy-1")
    assert policy is not None
    assert policy.approved is True
    assert policy.enabled is True


def test_automation_engine_disable_policy() -> None:
    """Test disabling a policy."""
    engine = AutomationEngine()
    engine.create_policy("policy-1", "trigger", "action")
    
    success = engine.disable_policy("policy-1")
    assert success is True
    
    policy = engine.get_policy("policy-1")
    assert policy is not None
    assert policy.enabled is False


def test_automation_engine_list_policies() -> None:
    """Test listing policies."""
    engine = AutomationEngine()
    engine.create_policy("policy-1", "trigger1", "action1")
    engine.create_policy("policy-2", "trigger2", "action2")
    engine.create_policy("policy-3", "trigger3", "action3")
    
    policies = engine.list_policies()
    assert len(policies) == 3


def test_automation_engine_delete_policy() -> None:
    """Test deleting a policy."""
    engine = AutomationEngine()
    engine.create_policy("policy-1", "trigger", "action")
    
    success = engine.delete_policy("policy-1")
    assert success is True
    
    policy = engine.get_policy("policy-1")
    assert policy is None


def test_automation_engine_execute_policy() -> None:
    """Test executing a policy."""
    engine = AutomationEngine()
    engine.create_policy("policy-1", "trigger", "action")
    engine.approve_policy("policy-1")
    
    result = engine.execute_policy("policy-1", {"test": "context"})
    assert result["success"] is True
    assert result["policy_id"] == "policy-1"


def test_automation_engine_execute_unapproved_policy() -> None:
    """Test executing unapproved policy fails."""
    engine = AutomationEngine()
    engine.create_policy("policy-1", "trigger", "action")
    
    result = engine.execute_policy("policy-1")
    assert result["success"] is False
    # A policy that's not approved is also disabled by default
    assert result["reason"] in ["policy_not_approved", "policy_disabled"]


def test_automation_engine_execute_disabled_policy() -> None:
    """Test executing disabled policy fails."""
    engine = AutomationEngine()
    engine.create_policy("policy-1", "trigger", "action")
    engine.approve_policy("policy-1")
    engine.disable_policy("policy-1")
    
    result = engine.execute_policy("policy-1")
    assert result["success"] is False
    assert result["reason"] == "policy_disabled"


def test_automation_engine_execution_log() -> None:
    """Test execution logging."""
    engine = AutomationEngine()
    engine.create_policy("policy-1", "trigger", "action")
    engine.approve_policy("policy-1")
    
    engine.execute_policy("policy-1")
    engine.execute_policy("policy-1")
    
    log = engine.get_execution_log()
    assert len(log) >= 2
    assert all(entry["status"] == "executed" for entry in log)


def test_automation_engine_status() -> None:
    """Test automation status."""
    engine = AutomationEngine()
    engine.create_policy("policy-1", "trigger", "action")
    engine.create_policy("policy-2", "trigger", "action")
    engine.approve_policy("policy-1")
    
    status = engine.policy_status()
    assert status["schema"] == "bingomate-automation-status/v1"
    assert status["total_policies"] == 2
    assert status["enabled_policies"] == 1
    assert status["approved_policies"] == 1

