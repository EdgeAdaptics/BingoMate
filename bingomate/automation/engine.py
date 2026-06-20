from __future__ import annotations


class AutomationEngine:
    def propose(self, trigger: str, action: str) -> dict[str, object]:
        return {
            "trigger": trigger,
            "action": action,
            "status": "proposed",
            "requires_user_approval": True,
        }
