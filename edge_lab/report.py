from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

from edge_lab.export import read_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an Edge Impact Lab telemetry summary.")
    parser.add_argument("--db", default="edge_lab.db", help="SQLite database path.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--out", help="Output file. Defaults to stdout.")
    args = parser.parse_args()

    rows = list(read_rows(Path(args.db)))
    summary = summarize_rows(rows)

    if args.out:
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as output:
            write_summary(summary, args.format, output)
    else:
        write_summary(summary, args.format, sys.stdout)

    return 0


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(row["status"] for row in rows)
    reasons = Counter(reason for row in rows for reason in row["reasons"])
    scenarios = Counter(row["payload"].get("scenario", "live") for row in rows)
    risks = [int(row["risk"]) for row in rows]
    timestamps = [float(row["ts"]) for row in rows]

    return {
        "readings": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "scenario_counts": dict(sorted(scenarios.items())),
        "max_risk": max(risks) if risks else 0,
        "avg_risk": round(statistics.fmean(risks), 2) if risks else 0.0,
        "top_reasons": reasons.most_common(5),
        "first_seen": format_ts(min(timestamps)) if timestamps else None,
        "last_seen": format_ts(max(timestamps)) if timestamps else None,
        "recommendation": build_recommendation(status_counts, risks, reasons),
    }


def write_summary(summary: dict[str, Any], output_format: str, output: TextIO) -> None:
    if output_format == "json":
        output.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        return

    output.write("# Edge Impact Lab Telemetry Summary\n\n")
    output.write(f"- Readings: {summary['readings']}\n")
    output.write(f"- Time window: {summary['first_seen'] or 'n/a'} to {summary['last_seen'] or 'n/a'}\n")
    output.write(f"- Max risk: {summary['max_risk']}\n")
    output.write(f"- Average risk: {summary['avg_risk']}\n")
    output.write(f"- Recommendation: {summary['recommendation']}\n\n")

    output.write("## Status Counts\n\n")
    write_dict_table(output, "Status", "Count", summary["status_counts"])

    output.write("\n## Scenario Counts\n\n")
    write_dict_table(output, "Scenario", "Count", summary["scenario_counts"])

    output.write("\n## Top Reasons\n\n")
    if summary["top_reasons"]:
        output.write("| Reason | Count |\n| --- | --- |\n")
        for reason, count in summary["top_reasons"]:
            output.write(f"| {reason} | {count} |\n")
    else:
        output.write("No reasons recorded.\n")


def write_dict_table(output: TextIO, key_label: str, value_label: str, values: dict[str, int]) -> None:
    if not values:
        output.write("No rows.\n")
        return
    output.write(f"| {key_label} | {value_label} |\n| --- | --- |\n")
    for key, value in values.items():
        output.write(f"| {key} | {value} |\n")


def build_recommendation(status_counts: Counter[str], risks: list[int], reasons: Counter[str]) -> str:
    if not risks:
        return "Collect telemetry before making a maintenance decision."
    if status_counts.get("ALERT", 0):
        return "Investigate alert readings before returning the asset to normal operation."
    if status_counts.get("WARN", 0):
        return "Schedule inspection and continue local monitoring."
    if reasons and reasons.most_common(1)[0][0] != "within baseline":
        return "Review recurring non-baseline reasons."
    return "Asset is within the current baseline."


def format_ts(value: float) -> str:
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    sys.exit(main())
