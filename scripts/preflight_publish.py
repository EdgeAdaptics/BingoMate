from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "exports", "build", "dist"}
SKIP_SUFFIXES = {".pyc", ".db", ".db-shm", ".db-wal", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"}
SECRET_ENV_NAMES = {"LAB_WIFI_PASSWORD", "EDGE_LAB_MQTT_PASSWORD"}
PLACEHOLDER_VALUES = {"", "<do-not-commit>", "your-lab-password"}


def main() -> int:
    findings: list[str] = []
    for path in iter_text_files(ROOT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        findings.extend(check_file(path, text))

    if findings:
        print("preflight failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("preflight passed")
    return 0


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def check_file(path: Path, text: str) -> list[str]:
    relative = path.relative_to(ROOT)
    findings: list[str] = []

    token_patterns = [
        ("OpenAI API key", r"\bs" + r"k-[A-Za-z0-9_-]{20,}"),
        ("GitHub token", r"\bg" + r"hp_[A-Za-z0-9_]{20,}"),
        ("GitHub fine-grained token", r"\bgithub" + r"_pat_[A-Za-z0-9_]{20,}"),
        ("lab Wi-Fi password", re.escape("My" + "Password") + r"@\d+"),
    ]
    for label, pattern in token_patterns:
        if re.search(pattern, text):
            findings.append(f"{relative}: contains possible {label}")

    for env_name in SECRET_ENV_NAMES:
        for match in re.finditer(rf"{env_name}[ \t]*=[ \t]*([^\r\n]*)", text):
            value = normalize_env_value(match.group(1))
            if value not in PLACEHOLDER_VALUES:
                findings.append(f"{relative}: contains non-placeholder {env_name}")

    if relative.name in {".env", ".env.local"}:
        findings.append(f"{relative}: env file should not be published")

    return findings


def normalize_env_value(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
