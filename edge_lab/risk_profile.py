from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RiskProfile:
    name: str = "default"
    vibration_warn_g: float = 1.4
    vibration_alert_g: float = 2.2
    temperature_warn_c: float = 40.0
    temperature_alert_c: float = 60.0
    humidity_alert_pct: float = 85.0
    sound_alert_level: float = 0.75
    warn_score: int = 30
    alert_score: int = 70


DEFAULT_RISK_PROFILE = RiskProfile()


def load_risk_profile(path: str | Path | None) -> RiskProfile:
    if not path:
        return DEFAULT_RISK_PROFILE

    profile_path = Path(path)
    with open(profile_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"{profile_path} must contain a JSON object")

    values: dict[str, Any] = {}
    for field_name in RiskProfile.__dataclass_fields__:
        if field_name in data:
            values[field_name] = data[field_name]
    return RiskProfile(**values)
