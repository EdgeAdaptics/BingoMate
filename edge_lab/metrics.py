from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from edge_lab.risk_profile import DEFAULT_RISK_PROFILE, RiskProfile


@dataclass(frozen=True)
class RiskResult:
    score: int
    status: str
    reasons: list[str]


def parse_sensor_line(line: str) -> dict[str, Any] | None:
    text = line.strip()
    if not text:
        return None

    if text.startswith("{") and text.endswith("}"):
        import json

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    payload: dict[str, Any] = {}
    for chunk in text.replace(",", " ").split():
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        payload[key.strip()] = _coerce_value(value.strip())

    return payload or {"message": text}


def score_reading(payload: dict[str, Any], profile: RiskProfile | None = None) -> RiskResult:
    active_profile = profile or DEFAULT_RISK_PROFILE
    score = 0
    reasons: list[str] = []

    vibration = _vibration_magnitude(payload)
    if vibration is not None:
        if vibration > active_profile.vibration_alert_g:
            score += 45
            reasons.append(f"high vibration {vibration:.2f}g")
        elif vibration > active_profile.vibration_warn_g:
            score += 20
            reasons.append(f"elevated vibration {vibration:.2f}g")

    temperature = _get_float(payload, "temperature_c", "temp_c", "temperature", "temp")
    if temperature is not None:
        if temperature >= active_profile.temperature_alert_c:
            score += 35
            reasons.append(f"high temperature {temperature:.1f}C")
        elif temperature >= active_profile.temperature_warn_c:
            score += 15
            reasons.append(f"warm enclosure {temperature:.1f}C")

    humidity = _get_float(payload, "humidity_pct", "humidity", "rh")
    if humidity is not None and humidity >= active_profile.humidity_alert_pct:
        score += 15
        reasons.append(f"humid air {humidity:.1f}%")

    sound = _get_float(payload, "sound_level", "sound", "mic")
    if sound is not None and sound > active_profile.sound_alert_level:
        score += 15
        reasons.append("sustained acoustic activity")

    score = max(0, min(score, 100))
    if score >= active_profile.alert_score:
        status = "ALERT"
    elif score >= active_profile.warn_score:
        status = "WARN"
    else:
        status = "OK"

    if not reasons:
        reasons.append("within baseline")

    return RiskResult(score=score, status=status, reasons=reasons)


def _vibration_magnitude(payload: dict[str, Any]) -> float | None:
    ax = _get_float(payload, "ax", "accel_x", "x")
    ay = _get_float(payload, "ay", "accel_y", "y")
    az = _get_float(payload, "az", "accel_z", "z")
    if ax is None or ay is None or az is None:
        return None
    return math.sqrt(ax * ax + ay * ay + az * az)


def _get_float(payload: dict[str, Any], *names: str) -> float | None:
    for name in names:
        if name not in payload:
            continue
        value = payload[name]
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue
    return None


def _coerce_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
