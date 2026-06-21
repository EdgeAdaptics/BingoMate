from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable, TextIO


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Edge Impact Lab telemetry.")
    parser.add_argument("--db", default="edge_lab.db", help="SQLite database path.")
    parser.add_argument("--format", choices=["csv", "jsonl"], default="csv")
    parser.add_argument("--out", help="Output file. Defaults to stdout.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum rows to export. 0 means all rows.")
    args = parser.parse_args()

    rows = list(read_rows(Path(args.db), args.limit))
    if args.out:
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="") as output:
            write_rows(rows, args.format, output)
    else:
        write_rows(rows, args.format, sys.stdout)

    return 0


def read_rows(db_path: Path, limit: int = 0) -> Iterable[dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    try:
        query = """
            SELECT id, ts, source, payload_json, risk, status, reasons_json
            FROM readings
            ORDER BY id ASC
        """
        params: tuple[int, ...] = ()
        if limit > 0:
            query += " LIMIT ?"
            params = (limit,)
        for row in conn.execute(query, params):
            reading_id, ts, source, payload_json, risk, status, reasons_json = row
            payload = json.loads(payload_json)
            reasons = json.loads(reasons_json)
            yield {
                "id": reading_id,
                "ts": ts,
                "source": source,
                "status": status,
                "risk": risk,
                "reasons": reasons,
                "payload": payload,
            }
    finally:
        conn.close()


def write_rows(rows: list[dict[str, Any]], output_format: str, output: TextIO) -> None:
    if output_format == "jsonl":
        for row in rows:
            output.write(json.dumps(row, sort_keys=True) + "\n")
        return

    fieldnames = sorted({key for row in rows for key in flatten_row(row).keys()})
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(flatten_row(row))


def flatten_row(row: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {
        "id": row["id"],
        "ts": row["ts"],
        "source": row["source"],
        "status": row["status"],
        "risk": row["risk"],
        "reasons": "; ".join(row["reasons"]),
    }
    for key, value in row["payload"].items():
        flat[f"payload_{key}"] = value
    return flat


if __name__ == "__main__":
    sys.exit(main())
