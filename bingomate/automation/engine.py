from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AutomationPolicy:
    id: str
    trigger: str
    action: str
    enabled: bool = True
    approved: bool = False
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "trigger": self.trigger,
            "action": self.action,
            "enabled": self.enabled,
            "approved": self.approved,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class AutomationEngine:
    def __init__(self) -> None:
        self._policies: dict[str, AutomationPolicy] = {}
        self._execution_log: list[dict[str, Any]] = []

    def propose(self, trigger: str, action: str) -> dict[str, object]:
        return {
            "trigger": trigger,
            "action": action,
            "status": "proposed",
            "requires_user_approval": True,
            "suggestions": [
                "Consider device state changes as triggers",
                "Chain multiple actions for complex workflows",
                "Test policies in simulation mode first",
            ],
        }

    def create_policy(
        self,
        policy_id: str,
        trigger: str,
        action: str,
        metadata: dict[str, Any] | None = None,
    ) -> AutomationPolicy:
        policy = AutomationPolicy(
            id=policy_id,
            trigger=trigger,
            action=action,
            enabled=False,
            approved=False,
            created_at=time.time(),
            metadata=metadata or {},
        )
        self._policies[policy_id] = policy
        return policy

    def approve_policy(self, policy_id: str) -> bool:
        if policy_id not in self._policies:
            return False
        policy = self._policies[policy_id]
        self._policies[policy_id] = AutomationPolicy(
            id=policy.id,
            trigger=policy.trigger,
            action=policy.action,
            enabled=True,
            approved=True,
            created_at=policy.created_at,
            metadata=policy.metadata,
        )
        return True

    def disable_policy(self, policy_id: str) -> bool:
        if policy_id not in self._policies:
            return False
        policy = self._policies[policy_id]
        self._policies[policy_id] = AutomationPolicy(
            id=policy.id,
            trigger=policy.trigger,
            action=policy.action,
            enabled=False,
            approved=policy.approved,
            created_at=policy.created_at,
            metadata=policy.metadata,
        )
        return True

    def list_policies(self) -> list[AutomationPolicy]:
        return sorted(self._policies.values(), key=lambda policy: policy.created_at, reverse=True)

    def get_policy(self, policy_id: str) -> AutomationPolicy | None:
        return self._policies.get(policy_id)

    def delete_policy(self, policy_id: str) -> bool:
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    def execute_policy(self, policy_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        policy = self._policies.get(policy_id)
        if not policy:
            return {"success": False, "reason": "policy_not_found"}

        if not policy.enabled:
            return {"success": False, "reason": "policy_disabled"}

        if not policy.approved:
            return {"success": False, "reason": "policy_not_approved"}

        execution_record = {
            "policy_id": policy_id,
            "trigger": policy.trigger,
            "action": policy.action,
            "executed_at": time.time(),
            "context": context or {},
            "status": "executed",
        }
        self._execution_log.append(execution_record)

        return {
            "success": True,
            "policy_id": policy_id,
            "trigger": policy.trigger,
            "action": policy.action,
            "status": "executed",
        }

    def get_execution_log(self, limit: int = 50) -> list[dict[str, Any]]:
        safe_limit = min(max(limit, 1), 500)
        return self._execution_log[-safe_limit:]

    def policy_status(self) -> dict[str, Any]:
        enabled_count = sum(1 for policy in self._policies.values() if policy.enabled)
        approved_count = sum(1 for policy in self._policies.values() if policy.approved)

        return {
            "schema": "bingomate-automation-status/v1",
            "total_policies": len(self._policies),
            "enabled_policies": enabled_count,
            "approved_policies": approved_count,
            "total_executions": len(self._execution_log),
            "recent_executions": self._execution_log[-10:],
        }
