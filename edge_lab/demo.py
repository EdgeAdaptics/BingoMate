from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from edge_lab.bridge import build_reading, init_db, persist_reading
from edge_lab.risk_profile import load_risk_profile


SCENARIOS: dict[str, list[dict[str, float | str]]] = {
    "baseline": [
        {"temperature_c": 30.2, "humidity_pct": 48.0, "ax": 0.02, "ay": 0.01, "az": 1.01, "sound_level": 0.12},
        {"temperature_c": 31.1, "humidity_pct": 50.2, "ax": 0.03, "ay": 0.02, "az": 1.00, "sound_level": 0.15},
        {"temperature_c": 31.4, "humidity_pct": 51.0, "ax": 0.04, "ay": 0.02, "az": 1.02, "sound_level": 0.17},
    ],
    "bearing_wear": [
        {"temperature_c": 38.5, "humidity_pct": 54.0, "ax": 0.45, "ay": 0.34, "az": 1.42, "sound_level": 0.52},
        {"temperature_c": 41.8, "humidity_pct": 55.2, "ax": 0.58, "ay": 0.41, "az": 1.62, "sound_level": 0.68},
        {"temperature_c": 44.0, "humidity_pct": 56.0, "ax": 0.64, "ay": 0.44, "az": 1.82, "sound_level": 0.74},
    ],
    "overheat": [
        {"temperature_c": 55.5, "humidity_pct": 60.0, "ax": 0.16, "ay": 0.10, "az": 1.03, "sound_level": 0.20},
        {"temperature_c": 61.2, "humidity_pct": 62.0, "ax": 0.18, "ay": 0.13, "az": 1.06, "sound_level": 0.23},
        {"temperature_c": 66.4, "humidity_pct": 63.5, "ax": 0.20, "ay": 0.14, "az": 1.07, "sound_level": 0.25},
    ],
    "impact_event": [
        {"temperature_c": 34.0, "humidity_pct": 52.0, "ax": 0.18, "ay": 0.12, "az": 1.04, "sound_level": 0.25},
        {"temperature_c": 61.0, "humidity_pct": 52.5, "ax": 1.20, "ay": 1.15, "az": 1.90, "sound_level": 0.92},
        {"temperature_c": 35.0, "humidity_pct": 52.8, "ax": 0.28, "ay": 0.21, "az": 1.14, "sound_level": 0.35},
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Edge Impact Lab demo telemetry.")
    parser.add_argument("--db", default="edge_lab.db", help="SQLite database path.")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="baseline")
    parser.add_argument("--all", action="store_true", help="Seed all scenarios in sequence.")
    parser.add_argument("--source", default="demo-seed")
    parser.add_argument("--risk-profile", help="Optional JSON risk profile for seeded status scoring.")
    args = parser.parse_args()

    db_path = Path(args.db)
    init_db(db_path)
    risk_profile = load_risk_profile(args.risk_profile)

    scenario_names = list(SCENARIOS) if args.all else [args.scenario]
    inserted = 0
    for scenario_name in scenario_names:
        for offset, payload in enumerate(SCENARIOS[scenario_name]):
            enriched = dict(payload)
            enriched["scenario"] = scenario_name
            enriched["sequence"] = offset
            reading = build_reading(args.source, enriched, risk_profile)
            reading.ts = time.time() - ((len(SCENARIOS[scenario_name]) - offset) * 2)
            persist_reading(db_path, reading)
            inserted += 1

    print(f"seeded {inserted} readings into {db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
