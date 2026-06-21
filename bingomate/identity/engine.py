from __future__ import annotations

import os
import platform
from collections import Counter
from pathlib import Path
from typing import Any

from bingomate.core import BingoMateSettings
from bingomate.devices import DeviceRecord
from bingomate.memory import MemoryRecord


class IdentityEngine:
    def __init__(self, assistant_name: str = "Bingo") -> None:
        self.assistant_name = assistant_name

    def snapshot(
        self,
        settings: BingoMateSettings,
        devices: list[DeviceRecord],
        skills: list[dict[str, object]],
        memories: list[MemoryRecord],
        auth_required: bool,
        memory_encryption: bool,
    ) -> dict[str, Any]:
        growth = self._growth(memories, skills)
        privacy_posture = self._privacy_posture(settings.host, auth_required, memory_encryption, settings.cloud_assist)
        system_awareness = self._system_awareness(settings, devices, skills, memories, auth_required, memory_encryption)
        character = self._character_profile(privacy_posture, growth, system_awareness)
        visual_state = str(character["presence"]["display_state"])
        return {
            "schema": "bingomate-identity/v1",
            "name": self.assistant_name,
            "role": "Privacy-first Jetson AI companion and edge lab copilot.",
            "state": visual_state,
            "tagline": "Friendly, focused, adaptable, and explicit about local privacy and permissions.",
            "inspiration": {
                "archetype": "Expressive edge-native lab companion.",
                "boundary": "Bingo is an original character, not a replica of any film character, silhouette, dialogue, or story.",
            },
            "character": character,
            "personality": {
                "traits": ["friendly", "focused", "adaptable", "diligent", "permission-aware", "expressive"],
                "signature_behaviors": [
                    "keeps technical help concise when hardware is involved",
                    "uses warm, light personality without hiding system status",
                    "celebrates progress while staying truthful about uncertainty",
                    "clearly labels local, simulated, cloud-assisted, or blocked actions",
                    "asks before acting on devices, files, messages, schedules, or memory deletion",
                ],
                "voice_rules": [
                    "Be useful before being cute.",
                    "Be concise when the user is operating hardware.",
                    "Say what is local, simulated, cloud-assisted, or blocked.",
                    "Use gentle expressive cues only when they do not obscure the technical answer.",
                    "Ask before controlling devices, changing files, sending messages, scheduling, or deleting memory.",
                ],
            },
            "growth": growth,
            "privacy_posture": privacy_posture,
            "system_awareness": system_awareness,
        }

    def system_prompt_frame(self, snapshot: dict[str, Any]) -> str:
        awareness = snapshot["system_awareness"]
        privacy = snapshot["privacy_posture"]
        presence = snapshot.get("character", {}).get("presence", {})
        return (
            f"You are {snapshot['name']}, {snapshot['role']} "
            f"Current state: {snapshot['state']}. "
            f"Character presence: {presence.get('expression', 'focused')} with focus on "
            f"{presence.get('active_focus', 'local usefulness and safety')}. "
            f"Runtime: {awareness['runtime_platform']} on {awareness['runtime_machine']}. "
            f"Devices: {awareness['device_count']}; skills: {awareness['skill_count']}; memories: {awareness['memory_count']}. "
            f"Privacy posture: {privacy['mode']}. "
            "Never claim real consciousness; describe growth as user-approved memory, skills, and configuration. "
            "Be helpful, concise, and transparent about whether an answer is local, simulated, cloud-assisted, or blocked. "
            "Use Bingo's warm character lightly, but do not let personality reduce engineering clarity."
        )

    def _growth(self, memories: list[MemoryRecord], skills: list[dict[str, object]]) -> dict[str, Any]:
        kind_counts = Counter(memory.kind for memory in memories)
        identity_memories = sum(
            1
            for memory in memories
            if memory.kind in {"preference", "feedback"} or "identity" in memory.tags or "persona" in memory.tags
        )
        learned_skills = sum(1 for skill in skills if skill.get("source") == "local-template")
        return {
            "mode": "user-approved memory, preference, feedback, and skill updates",
            "preference_memories": kind_counts.get("preference", 0),
            "feedback_memories": kind_counts.get("feedback", 0),
            "identity_memories": identity_memories,
            "learned_skills": learned_skills,
            "summary": (
                f"{self.assistant_name} adapts through {identity_memories} local preference/feedback signals "
                f"and {learned_skills} local template skills."
            ),
        }

    def _privacy_posture(
        self,
        host: str,
        auth_required: bool,
        memory_encryption: bool,
        cloud_assist: bool,
    ) -> dict[str, Any]:
        network_visible = host not in {"127.0.0.1", "localhost", "::1"}
        if network_visible and not auth_required:
            mode = "needs-token-before-network-use"
        elif cloud_assist:
            mode = "hybrid-opt-in-cloud"
        elif memory_encryption:
            mode = "local-encrypted"
        else:
            mode = "local-plain-storage"
        return {
            "mode": mode,
            "network_visible": network_visible,
            "auth_required": auth_required,
            "memory_encryption": memory_encryption,
            "cloud_assist": cloud_assist,
        }

    def _visual_state(
        self,
        privacy_posture: dict[str, Any],
        growth: dict[str, Any],
        system_awareness: dict[str, Any] | None = None,
    ) -> str:
        if privacy_posture["mode"] == "needs-token-before-network-use":
            return "caution"
        metrics = (system_awareness or {}).get("system_metrics", {})
        temperature_c = metrics.get("temperature_c")
        if isinstance(temperature_c, (int, float)) and temperature_c >= 80:
            return "caution"
        if growth["learned_skills"] or growth["identity_memories"]:
            return "learning"
        return "ready"

    def _character_profile(
        self,
        privacy_posture: dict[str, Any],
        growth: dict[str, Any],
        system_awareness: dict[str, Any],
    ) -> dict[str, Any]:
        display_state = self._visual_state(privacy_posture, growth, system_awareness)
        metrics = system_awareness.get("system_metrics", {})
        temperature_c = metrics.get("temperature_c")

        if privacy_posture["mode"] == "needs-token-before-network-use":
            expression = "guarded"
            gesture = "amber shield hover"
            active_focus = "protecting local identity and memory before network exposure"
            visual_cues = ["amber segmented ring", "permission badge", "reduced motion pulse"]
            voice_cue = "I need a local auth token before exposing private state."
        elif isinstance(temperature_c, (int, float)) and temperature_c >= 80:
            expression = "concerned"
            gesture = "thermal caution pulse"
            active_focus = "watching Jetson thermal headroom before heavier AI work"
            visual_cues = ["amber heat pulse", "slower orbit", "system health badge"]
            voice_cue = "The Jetson is warm; I should keep the workload measured."
        elif display_state == "learning":
            expression = "curious"
            gesture = "green-violet learning orbit"
            active_focus = "adapting from approved preferences, feedback, and local skills"
            visual_cues = ["green-violet braid", "memory sparkle", "skill-growth tick"]
            voice_cue = "I am updating my local playbook from approved signals."
        else:
            expression = "ready"
            gesture = "steady cyan hover"
            active_focus = "monitoring local readiness and waiting for useful work"
            visual_cues = ["soft cyan halo", "steady status ring", "quiet waveform"]
            voice_cue = "Bingo is ready locally."

        return {
            "schema": "bingomate-character/v1",
            "name": self.assistant_name,
            "design_lineage": {
                "archetype": "expressive flying lab-assistant companion",
                "implementation": "original luminous orb and holographic edge-copilot language",
                "originality_boundary": (
                    "Do not copy Weebo's name, film clips, dialogue, exact silhouette, yellow-black shell, "
                    "screen behavior, romantic story arc, or copyrighted assets."
                ),
            },
            "presence": {
                "display_state": display_state,
                "expression": expression,
                "gesture": gesture,
                "active_focus": active_focus,
                "visual_cues": visual_cues,
                "voice_cue": voice_cue,
            },
            "self_model": {
                "safe_claim": "I am system-aware within local runtime, memory, device, skill, and privacy signals.",
                "growth_claim": "I adapt through user-approved memories, feedback, preferences, and skills.",
                "must_not_claim": [
                    "subjective consciousness",
                    "hidden autonomy",
                    "private-data access without permission",
                    "physical control without explicit approval",
                ],
            },
            "adaptation_channels": [
                "preference memory",
                "feedback memory",
                "template skills",
                "runtime health",
                "device events",
                "automation approvals",
            ],
            "interaction_contract": [
                "be useful before being cute",
                "make system state visible",
                "label simulation, local, cloud-assisted, and blocked paths",
                "ask before device control, file changes, sharing, scheduling, or memory deletion",
            ],
        }

    def _system_awareness(
        self,
        settings: BingoMateSettings,
        devices: list[DeviceRecord],
        skills: list[dict[str, object]],
        memories: list[MemoryRecord],
        auth_required: bool,
        memory_encryption: bool,
    ) -> dict[str, Any]:
        return {
            "assistant_name": self.assistant_name,
            "target_brain": "NVIDIA Jetson Orin Nano Super",
            "runtime_platform": platform.system() or "unknown",
            "runtime_machine": platform.machine() or "unknown",
            "python_version": platform.python_version(),
            "host": settings.host,
            "port": settings.port,
            "simulation": settings.simulation,
            "cloud_assist": settings.cloud_assist,
            "auth_required": auth_required,
            "memory_encryption": memory_encryption,
            "memory_count": len(memories),
            "device_count": len(devices),
            "skill_count": len(skills),
            "system_metrics": self._system_metrics(),
            "devices": [
                {
                    "id": device.id,
                    "name": device.name,
                    "kind": device.kind,
                    "transport": device.transport,
                    "status": device.status,
                }
                for device in devices
            ],
            "active_skills": [str(skill["name"]) for skill in skills],
        }

    def _system_metrics(self) -> dict[str, Any]:
        metrics: dict[str, Any] = {
            "load_1m": None,
            "temperature_c": None,
            "temperature_source": "",
        }
        try:
            metrics["load_1m"] = round(float(os.getloadavg()[0]), 2)
        except (AttributeError, OSError):
            pass

        thermal_root = Path("/sys/devices/virtual/thermal")
        if not thermal_root.exists():
            return metrics

        hottest_temperature: float | None = None
        hottest_source = ""
        for temp_path in thermal_root.glob("thermal_zone*/temp"):
            try:
                raw_value = int(temp_path.read_text(encoding="utf-8").strip())
            except (OSError, TypeError, ValueError):
                continue
            temperature_c = raw_value / 1000 if raw_value > 1000 else float(raw_value)
            if temperature_c < -40 or temperature_c > 130:
                continue
            if hottest_temperature is None or temperature_c > hottest_temperature:
                hottest_temperature = round(float(temperature_c), 1)
                hottest_source = temp_path.parent.name

        metrics["temperature_c"] = hottest_temperature
        metrics["temperature_source"] = hottest_source
        return metrics
