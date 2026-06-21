#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER_NAME="${SUDO_USER:-$(whoami)}"
USER_HOME="$(getent passwd "${USER_NAME}" | cut -d: -f6)"
API_SERVICE_PATH="/etc/systemd/system/bingomate-api.service"
DISPLAY_SERVICE_PATH="/etc/systemd/system/bingomate-display.service"
PORT="${BINGOMATE_PORT:-8090}"
HOST="${BINGOMATE_HOST:-127.0.0.1}"

if [[ ! -x "${ROOT_DIR}/.venv/bin/bingomate-api" ]]; then
  echo "Missing virtualenv executable. Run scripts/jetson_prepare.sh first."
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
ExecStart=${ROOT_DIR}/.venv/bin/bingomate-api --host ${HOST} --port ${PORT}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

sudo tee "${DISPLAY_SERVICE_PATH}" >/dev/null <<SERVICE
[Unit]
Description=BingoMate boot display
After=graphical.target bingomate-api.service
Wants=bingomate-api.service

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${ROOT_DIR}
EnvironmentFile=-${ROOT_DIR}/.env.local
Environment=DISPLAY=:0
Environment=XAUTHORITY=${USER_HOME}/.Xauthority
ExecStart=/usr/bin/env bash ${ROOT_DIR}/scripts/bingomate_display_kiosk.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable --now bingomate-api.service
sudo systemctl enable --now bingomate-display.service
sudo systemctl status bingomate-api.service --no-pager
sudo systemctl status bingomate-display.service --no-pager
