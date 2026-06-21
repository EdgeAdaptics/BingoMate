#!/usr/bin/env python
"""Local development utilities for BingoMate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


BASE_URL = os.getenv("BINGOMATE_DEV_BASE_URL", "http://127.0.0.1:8090").rstrip("/")


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        body = response.read().decode("utf-8")
        return response.status, json.loads(body) if body else None


def health_check() -> bool:
    try:
        status, data = request_json("GET", "/healthz")
    except (OSError, urllib.error.URLError) as exc:
        print("[FAIL] API server is not running")
        print("       Start with: python -m bingomate.cli --host 127.0.0.1 --port 8090")
        print(f"       Error: {exc}")
        return False
    if status != 200:
        print(f"[FAIL] Health endpoint returned HTTP {status}")
        return False
    print("[PASS] API server is healthy")
    print(f"       Assistant: {data.get('assistant')}")
    print(f"       Mode: {'Simulation' if data.get('simulation') else 'Live'}")
    return True


def run_check(label: str, func) -> bool:
    try:
        detail = func()
    except Exception as exc:
        print(f"[FAIL] {label}: {exc}")
        return False
    suffix = f" ({detail})" if detail else ""
    print(f"[PASS] {label}{suffix}")
    return True


def test_api() -> bool:
    checks = [
        ("Health check", lambda: assert_status("GET", "/healthz")),
        ("Reasoning status", lambda: assert_schema("GET", "/api/reasoning/status", "bingomate-reasoning-status/v1")),
        ("Voice STT status", lambda: assert_key("GET", "/api/voice/stt/status", "wake_word")),
        (
            "Create memory",
            lambda: assert_status(
                "POST",
                "/api/memories",
                {"kind": "test", "content": "Test memory from dev_utils", "importance": 1},
            ),
        ),
        ("List skills", lambda: f"{len(assert_list('GET', '/api/skills'))} available"),
        ("Run echo skill", lambda: assert_status("POST", "/api/skills/echo/run", {"prompt": "Hello", "context": {}})),
        ("List devices", lambda: f"{len(assert_list('GET', '/api/devices'))} seeded"),
        ("Automation status", lambda: assert_schema("GET", "/api/automations/status", "bingomate-automation-status/v1")),
    ]
    passed = sum(1 for label, func in checks if run_check(label, func))
    print(f"\n{passed}/{len(checks)} checks passed")
    return passed == len(checks)


def assert_status(method: str, path: str, payload: dict[str, Any] | None = None) -> str:
    status, _ = request_json(method, path, payload)
    if status != 200:
        raise RuntimeError(f"HTTP {status}")
    return ""


def assert_schema(method: str, path: str, schema: str) -> str:
    status, data = request_json(method, path)
    if status != 200:
        raise RuntimeError(f"HTTP {status}")
    if data.get("schema") != schema:
        raise RuntimeError(f"unexpected schema {data.get('schema')}")
    return schema


def assert_key(method: str, path: str, key: str) -> str:
    status, data = request_json(method, path)
    if status != 200:
        raise RuntimeError(f"HTTP {status}")
    if key not in data:
        raise RuntimeError(f"missing key {key}")
    return key


def assert_list(method: str, path: str) -> list[Any]:
    status, data = request_json(method, path)
    if status != 200:
        raise RuntimeError(f"HTTP {status}")
    if not isinstance(data, list):
        raise RuntimeError("expected list response")
    return data


def seed_memories() -> bool:
    memories = [
        {"kind": "note", "content": "Jetson Orin Nano is a powerful edge compute platform", "importance": 2, "tags": ["jetson", "hardware", "edge"]},
        {"kind": "note", "content": "Privacy-first architecture keeps data local", "importance": 2, "tags": ["privacy", "security", "edge"]},
        {"kind": "reminder", "content": "Update Jetson firmware monthly", "importance": 1, "tags": ["maintenance", "jetson", "firmware"]},
        {"kind": "note", "content": "BingoMate supports voice, vision, and automation", "importance": 2, "tags": ["features", "bingomate"]},
        {"kind": "note", "content": "Local LLM integration enables private reasoning", "importance": 2, "tags": ["ai", "llm", "privacy"]},
    ]
    created = 0
    for memory in memories:
        try:
            assert_status("POST", "/api/memories", memory)
            created += 1
            print(f"[PASS] Created: {memory['content'][:50]}...")
        except Exception as exc:
            print(f"[FAIL] Failed to create memory: {exc}")
    print(f"\nSeeded {created}/{len(memories)} memories")
    return created == len(memories)


def load_sample_policies() -> bool:
    policies = [
        {"trigger": "device_online", "action": "log_event", "approved": False},
        {"trigger": "temperature_alert", "action": "notify_user", "approved": False},
        {"trigger": "daily_schedule", "action": "run_diagnostic", "approved": False},
    ]
    created = 0
    for policy in policies:
        try:
            _, data = request_json("POST", "/api/automations/policies", policy)
            created += 1
            print(f"[PASS] Created policy: {data['policy_id']}")
            print(f"       Trigger: {policy['trigger']} -> {policy['action']}")
        except Exception as exc:
            print(f"[FAIL] Failed to create policy: {exc}")
    print(f"\nLoaded {created}/{len(policies)} automation policies")
    return created == len(policies)


def test_voice_simulation() -> bool:
    query = urllib.parse.quote("hey bingo what is your status")
    try:
        _, data = request_json("GET", f"/api/voice/simulate?text={query}")
    except Exception as exc:
        print(f"[FAIL] Voice simulation: {exc}")
        return False
    print("[PASS] Voice simulation")
    print(f"       Wake word detected: {data.get('wake_detected')}")
    print(f"       Transcript: {data.get('text')}")
    print(f"       Mode: {data.get('mode')}")
    return True


def test_vision_simulation() -> bool:
    try:
        _, data = request_json("GET", "/api/vision/simulate?label=desk")
    except Exception as exc:
        print(f"[FAIL] Vision simulation: {exc}")
        return False
    print("[PASS] Vision simulation")
    print(f"       Scene: {data.get('scene')}")
    print(f"       Objects: {', '.join(data.get('objects', []))}")
    print(f"       Detections: {len(data.get('detections', []))}")
    return True


def start_api() -> bool:
    print("Starting BingoMate API server...")
    try:
        subprocess.Popen(
            [sys.executable, "-m", "bingomate.cli", "--host", "127.0.0.1", "--port", "8090"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(2)
        return health_check()
    except Exception as exc:
        print(f"[FAIL] Failed to start API: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="BingoMate development utilities")
    parser.add_argument(
        "command",
        choices=["health-check", "test-api", "seed-memories", "load-policies", "test-voice", "test-vision", "start-api"],
        help="Command to run",
    )
    args = parser.parse_args()
    handlers = {
        "health-check": health_check,
        "test-api": test_api,
        "seed-memories": seed_memories,
        "load-policies": load_sample_policies,
        "test-voice": test_voice_simulation,
        "test-vision": test_vision_simulation,
        "start-api": start_api,
    }
    return 0 if handlers[args.command]() else 1


if __name__ == "__main__":
    raise SystemExit(main())
