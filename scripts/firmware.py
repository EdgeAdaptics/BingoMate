from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "firmware" / "manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Edge Impact Lab firmware with Arduino CLI.")
    parser.add_argument("action", choices=["list", "install", "compile", "upload", "command"])
    parser.add_argument("--sketch", choices=sorted(load_manifest()["sketches"]), help="Sketch key from firmware/manifest.json.")
    parser.add_argument("--port", help="Serial port for upload.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    args = parser.parse_args()

    manifest = load_manifest()
    if args.action == "list":
        return list_sketches(manifest)

    if not args.sketch:
        raise SystemExit("--sketch is required for this action")

    sketch = manifest["sketches"][args.sketch]
    commands = build_commands(args.action, sketch, args.port)
    if args.action == "command" or args.dry_run:
        for command in commands:
            print(format_command(command))
        return 0

    arduino_cli = shutil.which("arduino-cli")
    if not arduino_cli:
        raise SystemExit("arduino-cli is not installed or not on PATH")

    for command in commands:
        print(format_command(command))
        subprocess.run(command, cwd=ROOT, check=True)

    return 0


def load_manifest() -> dict[str, Any]:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def list_sketches(manifest: dict[str, Any]) -> int:
    for name, sketch in manifest["sketches"].items():
        print(f"{name}\t{sketch['fqbn']}\t{sketch['description']}")
    return 0


def build_commands(action: str, sketch: dict[str, Any], port: str | None = None) -> list[list[str]]:
    fqbn = sketch["fqbn"]
    sketch_path = str(ROOT / sketch["path"])
    commands: list[list[str]] = []

    if action == "install":
        if sketch.get("core_index_url"):
            commands.append(["arduino-cli", "core", "update-index", "--additional-urls", sketch["core_index_url"]])
            commands.append(["arduino-cli", "core", "install", sketch["core"], "--additional-urls", sketch["core_index_url"]])
        else:
            commands.append(["arduino-cli", "core", "update-index"])
            commands.append(["arduino-cli", "core", "install", sketch["core"]])
        for library in sketch.get("libraries", []):
            commands.append(["arduino-cli", "lib", "install", library])
    elif action == "compile":
        commands.append(["arduino-cli", "compile", "--fqbn", fqbn, sketch_path])
    elif action == "upload":
        upload_port = port or sketch.get("default_port_hint")
        if not upload_port:
            raise SystemExit("--port is required for upload")
        commands.append(["arduino-cli", "upload", "-p", upload_port, "--fqbn", fqbn, sketch_path])
    elif action == "command":
        commands.append(["arduino-cli", "compile", "--fqbn", fqbn, sketch_path])
        upload_port = port or sketch.get("default_port_hint", "<port>")
        commands.append(["arduino-cli", "upload", "-p", upload_port, "--fqbn", fqbn, sketch_path])
    else:
        raise ValueError(action)

    return commands


def format_command(command: list[str]) -> str:
    return " ".join(quote_arg(part) for part in command)


def quote_arg(value: str) -> str:
    if not value or any(char.isspace() for char in value):
        return '"' + value.replace('"', '\\"') + '"'
    return value


if __name__ == "__main__":
    raise SystemExit(main())
