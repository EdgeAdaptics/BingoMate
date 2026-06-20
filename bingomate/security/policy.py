from __future__ import annotations


class SecurityPolicy:
    def can_execute_action(self, action: str, approved: bool) -> bool:
        sensitive = {"send_message", "schedule_reminder", "control_device", "delete_memory"}
        action_text = action.lower()
        touches_device = any(token in action_text for token in ("esp32", "matrix", "arduino", "gpio", "relay", "motor", "device"))
        if action in sensitive or touches_device:
            return approved
        return True
