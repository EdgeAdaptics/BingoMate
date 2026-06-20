from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, TextIO

from serial.tools import list_ports

from edge_lab.node import collect_node_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Edge Impact Lab readiness checks.")
    parser.add_argument("--db", default="edge_lab.db", help="SQLite database path to inspect.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--out", help="Output file. Defaults to stdout.")
    args = parser.parse_args()

    report = build_doctor_report(Path(args.db))
    if args.out:
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as output:
            write_doctor_report(report, args.format, output)
    else:
        write_doctor_report(report, args.format, sys.stdout)

    return 0 if report["ready"] else 2


def build_doctor_report(db_path: Path) -> dict[str, Any]:
    checks = [
        check_python(),
        check_pyserial(),
        check_mqtt_dependency(),
        check_serial_ports(),
        check_database(db_path),
        check_publish_preflight(),
    ]
    return {
        "schema": "edge-impact-doctor/v1",
        "ready": all(check["status"] != "fail" for check in checks),
        "checks": checks,
        "node": collect_node_snapshot(),
    }


def check_python() -> dict[str, str]:
    version = sys.version.split()[0]
    status = "pass" if sys.version_info >= (3, 10) else "fail"
    return {"name": "python", "status": status, "detail": version}


def check_pyserial() -> dict[str, str]:
    status = "pass" if module_available("serial") else "fail"
    return {"name": "pyserial", "status": status, "detail": "installed" if status == "pass" else "missing"}


def check_mqtt_dependency() -> dict[str, str]:
    status = "pass" if module_available("paho.mqtt.client") else "warn"
    detail = "installed" if status == "pass" else "optional paho-mqtt not installed"
    return {"name": "mqtt_optional", "status": status, "detail": detail}


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def check_serial_ports() -> dict[str, Any]:
    ports = [
        {"device": port.device, "description": port.description, "hwid": port.hwid}
        for port in list_ports.comports()
    ]
    status = "pass" if ports else "warn"
    return {"name": "serial_ports", "status": status, "detail": f"{len(ports)} detected", "ports": ports}


def check_database(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        return {"name": "database", "status": "warn", "detail": f"{db_path} not found yet"}

    try:
        conn = sqlite3.connect(db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error as exc:
        return {"name": "database", "status": "fail", "detail": str(exc)}

    return {"name": "database", "status": "pass", "detail": f"{count} readings"}


def check_publish_preflight() -> dict[str, str]:
    script = Path(__file__).resolve().parents[1] / "scripts" / "preflight_publish.py"
    if not script.exists():
        return {"name": "publish_preflight", "status": "warn", "detail": "script missing"}

    python = shutil.which("python") or sys.executable
    result = subprocess.run(
        [python, str(script)],
        cwd=script.parents[1],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if result.returncode == 0:
        return {"name": "publish_preflight", "status": "pass", "detail": "passed"}
    return {"name": "publish_preflight", "status": "fail", "detail": (result.stdout + result.stderr).strip()}


def write_doctor_report(report: dict[str, Any], output_format: str, output: TextIO) -> None:
    if output_format == "json":
        output.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        return

    output.write("# Edge Impact Lab Doctor\n\n")
    output.write(f"- Ready: {'yes' if report['ready'] else 'no'}\n")
    output.write(f"- Hostname: {report['node'].get('hostname', 'unknown')}\n")
    output.write(f"- Platform: {report['node'].get('platform', 'unknown')}\n\n")
    output.write("| Check | Status | Detail |\n| --- | --- | --- |\n")
    for check in report["checks"]:
        output.write(f"| {check['name']} | {check['status']} | {check['detail']} |\n")

    serial_check = next((check for check in report["checks"] if check["name"] == "serial_ports"), None)
    if serial_check and serial_check.get("ports"):
        output.write("\n## Serial Ports\n\n")
        output.write("| Device | Description | Hardware ID |\n| --- | --- | --- |\n")
        for port in serial_check["ports"]:
            output.write(f"| {port['device']} | {port['description']} | {port['hwid']} |\n")


if __name__ == "__main__":
    raise SystemExit(main())
