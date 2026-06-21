from __future__ import annotations

import glob
import os
import platform
import shutil
import subprocess
import sys
from typing import Any


def collect_node_snapshot() -> dict[str, Any]:
    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "serial_devices": sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")),
        "i2c_devices": sorted(glob.glob("/dev/i2c-*")),
        "nvidia": collect_nvidia_snapshot(),
    }


def collect_nvidia_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "tegrastats_available": shutil.which("tegrastats") is not None,
        "nv_tegra_release": read_text_if_exists("/etc/nv_tegra_release"),
    }
    if snapshot["tegrastats_available"]:
        try:
            result = subprocess.run(
                ["tegrastats"],
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
            )
            snapshot["tegrastats"] = result.stdout.strip().splitlines()[:2]
        except (OSError, subprocess.SubprocessError) as exc:
            snapshot["tegrastats_error"] = str(exc)
    return snapshot


def read_text_if_exists(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except OSError:
        return None
