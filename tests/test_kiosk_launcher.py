"""Tests for the Jetson kiosk display launcher."""

from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def write_executable(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8", newline="\n")
    path.chmod(0o755)


def test_kiosk_launcher_accepts_python_health_fallback(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("launcher test runs in POSIX bash environments")

    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is required to exercise the kiosk launcher")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    capture_path = tmp_path / "browser-args.txt"

    write_executable(
        bin_dir / "curl",
        """
        #!/usr/bin/env bash
        exit 1
        """,
    )
    write_executable(
        bin_dir / "python3",
        """
        #!/usr/bin/env bash
        cat >/dev/null
        exit 0
        """,
    )
    write_executable(
        bin_dir / "sleep",
        """
        #!/usr/bin/env bash
        exit 0
        """,
    )
    write_executable(
        bin_dir / "chromium-browser",
        """
        #!/usr/bin/env bash
        printf '%s\\n' "$@" >"${BINGOMATE_BROWSER_CAPTURE}"
        exit 0
        """,
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["BINGOMATE_BROWSER_CAPTURE"] = str(capture_path)
    env["BINGOMATE_PORT"] = "8090"

    result = subprocess.run(
        [bash, str(ROOT / "scripts" / "bingomate_display_kiosk.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    browser_args = capture_path.read_text(encoding="utf-8")
    assert "--kiosk" in browser_args
    assert "http://127.0.0.1:8090/display" in browser_args
