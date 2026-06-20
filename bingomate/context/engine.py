from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any

from bingomate.core import BingoMateSettings
from bingomate.devices import DeviceRecord
from bingomate.events import EventRecord
from bingomate.memory import MemoryRecord


@dataclass(frozen=True)
class ContextSignal:
    source: str
    kind: str
    summary: str
    confidence: float
    privacy: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class AssistanceSuggestion:
    id: str
    title: str
    description: str
    category: str
    priority: str
    requires_approval: bool
    action: str
    reason: str
    source_signals: list[str]


class ContextEngine:
    def build_snapshot(
        self,
        settings: BingoMateSettings,
        identity: dict[str, Any],
        devices: list[DeviceRecord],
        skills: list[dict[str, object]],
        memories: list[MemoryRecord],
        events: list[EventRecord],
        voice_sample: dict[str, object],
        vision_sample: dict[str, object],
        auth_required: bool,
        memory_encryption: bool,
    ) -> dict[str, Any]:
        signals = self._signals(
            settings=settings,
            identity=identity,
            devices=devices,
            skills=skills,
            memories=memories,
            events=events,
            voice_sample=voice_sample,
            vision_sample=vision_sample,
            auth_required=auth_required,
            memory_encryption=memory_encryption,
        )
        suggestions = self.suggest(
            settings=settings,
            identity=identity,
            devices=devices,
            skills=skills,
            memories=memories,
            events=events,
            voice_sample=voice_sample,
            vision_sample=vision_sample,
            auth_required=auth_required,
            memory_encryption=memory_encryption,
            signals=signals,
        )
        return {
            "schema": "bingomate-context/v1",
            "mode": "local-simulation" if settings.simulation else "local-live",
            "generated_at": time.time(),
            "privacy": "local_only",
            "voice": voice_sample,
            "vision": vision_sample,
            "counts": {
                "devices": len(devices),
                "skills": len(skills),
                "memories": len(memories),
                "events": len(events),
                "signals": len(signals),
                "suggestions": len(suggestions),
            },
            "signals": [asdict(signal) for signal in signals],
            "suggestions": [asdict(suggestion) for suggestion in suggestions],
        }

    def suggest(
        self,
        settings: BingoMateSettings,
        identity: dict[str, Any],
        devices: list[DeviceRecord],
        skills: list[dict[str, object]],
        memories: list[MemoryRecord],
        events: list[EventRecord],
        voice_sample: dict[str, object],
        vision_sample: dict[str, object],
        auth_required: bool,
        memory_encryption: bool,
        signals: list[ContextSignal] | None = None,
    ) -> list[AssistanceSuggestion]:
        active_signals = signals or self._signals(
            settings=settings,
            identity=identity,
            devices=devices,
            skills=skills,
            memories=memories,
            events=events,
            voice_sample=voice_sample,
            vision_sample=vision_sample,
            auth_required=auth_required,
            memory_encryption=memory_encryption,
        )
        source_ids = [signal.kind for signal in active_signals]
        suggestions: list[AssistanceSuggestion] = []

        network_visible = settings.host not in {"127.0.0.1", "localhost", "::1"}
        if network_visible and not auth_required:
            suggestions.append(
                AssistanceSuggestion(
                    id="secure-network-dashboard",
                    title="Protect the dashboard before lab-network exposure",
                    description="BingoMate is reachable beyond localhost without a local API token.",
                    category="security",
                    priority="high",
                    requires_approval=True,
                    action="Set BINGOMATE_AUTH_TOKEN before exposing the dashboard on Wi-Fi.",
                    reason="Local runtime and device metadata should not be available to other lab clients by default.",
                    source_signals=source_ids,
                )
            )
        elif not auth_required:
            suggestions.append(
                AssistanceSuggestion(
                    id="set-local-token",
                    title="Set a local dashboard token before demos",
                    description="The service is local-only now, but demos often move from localhost to a lab network.",
                    category="privacy",
                    priority="medium",
                    requires_approval=True,
                    action="Set BINGOMATE_AUTH_TOKEN and restart BingoMate before sharing the dashboard.",
                    reason="Keeps private memory, devices, skills, and identity metadata protected.",
                    source_signals=["privacy"],
                )
            )

        if not memory_encryption:
            suggestions.append(
                AssistanceSuggestion(
                    id="enable-memory-encryption",
                    title="Enable encrypted memory for real personal data",
                    description="Local memory is currently stored without a configured encryption key.",
                    category="privacy",
                    priority="high",
                    requires_approval=True,
                    action="Set BINGOMATE_MEMORY_KEY before storing sensitive preferences, routines, or episodic memories.",
                    reason="The assistant is privacy-first; encryption should be enabled before meaningful personal use.",
                    source_signals=["memory"],
                )
            )

        if self._all_devices_simulated(devices):
            suggestions.append(
                AssistanceSuggestion(
                    id="bring-up-hardware",
                    title="Run physical hardware bring-up",
                    description="Jetson, ESP32 matrix, and Arduino nodes are visible as simulated records.",
                    category="hardware",
                    priority="medium",
                    requires_approval=False,
                    action="Run inventory and bridge checks, then register real ESP32/Arduino messages with signed device intake.",
                    reason="Moving from simulation to signed physical telemetry makes the lab showcase credible.",
                    source_signals=["devices", "events"],
                )
            )

        if not any(skill.get("source") == "local-template" for skill in skills):
            suggestions.append(
                AssistanceSuggestion(
                    id="teach-first-skill",
                    title="Teach Bingo one reusable lab skill",
                    description="No user-created template skills are active yet.",
                    category="learning",
                    priority="medium",
                    requires_approval=False,
                    action="Create a local template skill such as daily_lab_brief or field_diagnostics_summary.",
                    reason="Skills make Bingo visibly adaptable without executing arbitrary code.",
                    source_signals=["skills"],
                )
            )

        if not any(memory.kind == "preference" for memory in memories):
            suggestions.append(
                AssistanceSuggestion(
                    id="add-preference-memory",
                    title="Store one user-approved preference",
                    description="Bingo has no preference memory to adapt her responses.",
                    category="memory",
                    priority="low",
                    requires_approval=False,
                    action="Add a preference such as preferred demo style, reporting format, or privacy posture.",
                    reason="Preference memory is the safest first step toward useful personalization.",
                    source_signals=["memory"],
                )
            )

        alert_events = self._alert_events(events)
        if alert_events:
            suggestions.append(
                AssistanceSuggestion(
                    id="review-device-alerts",
                    title="Review recent device alerts",
                    description=f"{len(alert_events)} recent device event(s) look like WARN or ALERT telemetry.",
                    category="industrial-iot",
                    priority="high",
                    requires_approval=True,
                    action="Inspect recent device.message payloads before triggering physical automation.",
                    reason="Industrial IoT assistance should surface anomalies but require confirmation before device action.",
                    source_signals=["events", "devices"],
                )
            )

        if voice_sample.get("wake_word_detected") and vision_sample.get("scene"):
            suggestions.append(
                AssistanceSuggestion(
                    id="prepare-hands-free-summary",
                    title="Prepare a hands-free context summary",
                    description="Wake word and scene context are available in the same local snapshot.",
                    category="companion",
                    priority="low",
                    requires_approval=False,
                    action="Summarize voice request, scene objects, memory count, active skills, and device state.",
                    reason="This demonstrates multimodal context awareness while staying offline and local.",
                    source_signals=["voice", "vision", "memory", "devices"],
                )
            )

        return sorted(suggestions, key=lambda item: _priority_rank(item.priority))

    def _signals(
        self,
        settings: BingoMateSettings,
        identity: dict[str, Any],
        devices: list[DeviceRecord],
        skills: list[dict[str, object]],
        memories: list[MemoryRecord],
        events: list[EventRecord],
        voice_sample: dict[str, object],
        vision_sample: dict[str, object],
        auth_required: bool,
        memory_encryption: bool,
    ) -> list[ContextSignal]:
        signals = [
            ContextSignal(
                source="voice",
                kind="wake_word" if voice_sample.get("wake_word_detected") else "voice_idle",
                summary=str(voice_sample.get("text", "")) or "No voice text supplied.",
                confidence=0.9 if voice_sample.get("wake_word_detected") else 0.4,
                privacy="local_only",
                metadata=voice_sample,
            ),
            ContextSignal(
                source="vision",
                kind="scene",
                summary=f"Scene {vision_sample.get('scene', 'unknown')} with {len(vision_sample.get('objects', []))} object(s).",
                confidence=0.7,
                privacy="local_only",
                metadata=vision_sample,
            ),
            ContextSignal(
                source="identity",
                kind=str(identity.get("state", "ready")),
                summary=str(identity.get("tagline", "Bingo identity is available.")),
                confidence=0.8,
                privacy="local_only",
                metadata={"privacy_posture": identity.get("privacy_posture", {})},
            ),
            ContextSignal(
                source="privacy",
                kind="protected" if auth_required and memory_encryption else "needs_review",
                summary=f"Auth required: {auth_required}; memory encryption: {memory_encryption}.",
                confidence=1.0,
                privacy="local_only",
                metadata={"host": settings.host, "auth_required": auth_required, "memory_encryption": memory_encryption},
            ),
            ContextSignal(
                source="devices",
                kind="simulated" if self._all_devices_simulated(devices) else "live_or_mixed",
                summary=f"{len(devices)} device record(s), {self._simulated_device_count(devices)} simulated.",
                confidence=0.8,
                privacy="local_only",
                metadata={"device_ids": [device.id for device in devices]},
            ),
            ContextSignal(
                source="memory",
                kind="memory_profile",
                summary=f"{len(memories)} local memory record(s) available.",
                confidence=0.8,
                privacy="local_only",
                metadata={"kinds": sorted({memory.kind for memory in memories})},
            ),
            ContextSignal(
                source="skills",
                kind="skill_profile",
                summary=f"{len(skills)} active skill(s), {sum(1 for skill in skills if skill.get('requires_approval'))} approval-gated.",
                confidence=0.8,
                privacy="local_only",
                metadata={"names": [str(skill.get("name", "")) for skill in skills]},
            ),
            ContextSignal(
                source="events",
                kind="event_profile",
                summary=f"{len(events)} recent event(s), {len(self._alert_events(events))} alert-like.",
                confidence=0.7,
                privacy="local_only",
                metadata={"recent_kinds": [event.kind for event in events[-10:]]},
            ),
        ]
        return signals

    def _all_devices_simulated(self, devices: list[DeviceRecord]) -> bool:
        return bool(devices) and all(bool(device.metadata.get("simulation")) for device in devices)

    def _simulated_device_count(self, devices: list[DeviceRecord]) -> int:
        return sum(1 for device in devices if device.metadata.get("simulation"))

    def _alert_events(self, events: list[EventRecord]) -> list[EventRecord]:
        alert_events: list[EventRecord] = []
        for event in events:
            payload = event.payload.get("payload", event.payload)
            status = str(payload.get("status", "")).upper() if isinstance(payload, dict) else ""
            risk = payload.get("risk") if isinstance(payload, dict) else None
            if status in {"WARN", "ALERT"} or _numeric_risk(risk) >= 70:
                alert_events.append(event)
        return alert_events


def _numeric_risk(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _priority_rank(priority: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(priority, 3)
