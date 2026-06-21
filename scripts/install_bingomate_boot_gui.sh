#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER_NAME="${SUDO_USER:-$(whoami)}"
USER_HOME="$(getent passwd "${USER_NAME}" | cut -d: -f6)"
PORT="${BINGOMATE_PORT:-8090}"
HOST="${BINGOMATE_HOST:-127.0.0.1}"
API_SERVICE_PATH="/etc/systemd/system/bingomate-api.service"
AUTOSTART_DIR="${USER_HOME}/.config/autostart"
AUTOSTART_PATH="${AUTOSTART_DIR}/bingomate-display.desktop"

if [[ ! -x "${ROOT_DIR}/.venv/bin/bingomate-api" ]]; then
  echo "Missing virtualenv executable. Run scripts/jetson_prepare.sh first."
  exit 1
fi

if ! command -v chromium-browser >/dev/null 2>&1 && ! command -v chromium >/dev/null 2>&1; then
  echo "No Chromium-compatible browser found. Install chromium-browser or chromium first."
  exit 1
fi

sudo tee "${API_SERVICE_PATH}" >/dev/null <<SERVICE
[Unit]
Description=BingoMate local API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${ROOT_DIR}
EnvironmentFile=-${ROOT_DIR}/.env.local
Environment=BINGOMATE_HOST=${HOST}
Environment=BINGOMATE_PORT=${PORT}
ExecStart=${ROOT_DIR}/.venv/bin/bingomate-api --host \${BINGOMATE_HOST} --port \${BINGOMATE_PORT}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable --now bingomate-api.service

install -d -m 755 "${AUTOSTART_DIR}"
cat >"${AUTOSTART_PATH}" <<DESKTOP
[Desktop Entry]
Type=Application
Name=BingoMate Display
Comment=Launch BingoMate full-screen character display
Exec=/usr/bin/env BINGOMATE_PORT=${PORT} BINGOMATE_HOST=${HOST} /usr/bin/bash ${ROOT_DIR}/scripts/bingomate_display_kiosk.sh
Terminal=false
X-GNOME-Autostart-enabled=true
DESKTOP
chown "${USER_NAME}:${USER_NAME}" "${AUTOSTART_PATH}"

if [[ "${ENABLE_GDM_AUTOLOGIN:-0}" = "1" ]]; then
  sudo cp /etc/gdm3/custom.conf "/etc/gdm3/custom.conf.bingomate.$(date +%Y%m%d%H%M%S)"
  sudo python3 - "${USER_NAME}" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

user = sys.argv[1]
path = Path("/etc/gdm3/custom.conf")
lines = path.read_text(encoding="utf-8").splitlines()
output: list[str] = []
in_daemon = False
seen_daemon = False
keys = {
    "AutomaticLoginEnable": "AutomaticLoginEnable = true",
    "AutomaticLogin": f"AutomaticLogin = {user}",
}
written: set[str] = set()
for line in lines:
    stripped = line.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        if in_daemon:
            for key, value in keys.items():
                if key not in written:
                    output.append(value)
        in_daemon = stripped == "[daemon]"
        seen_daemon = seen_daemon or in_daemon
        output.append(line)
        continue
    if in_daemon and any(stripped.startswith(f"{key}") or stripped.startswith(f"#{key}") for key in keys):
        key = stripped.lstrip("#").split("=", 1)[0].strip()
        output.append(keys[key])
        written.add(key)
    else:
        output.append(line)
if not seen_daemon:
    output.extend(["", "[daemon]"])
    in_daemon = True
if in_daemon:
    for key, value in keys.items():
        if key not in written:
            output.append(value)
path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
PY
  sudo systemctl set-default graphical.target
fi

echo "BingoMate API service is enabled."
echo "Desktop autostart installed at ${AUTOSTART_PATH}."
echo "If ENABLE_GDM_AUTOLOGIN=1 was set, the Jetson will boot into the ${USER_NAME} desktop session."
echo "Reboot or log into the desktop session to launch the kiosk display."
