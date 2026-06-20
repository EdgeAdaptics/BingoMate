#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="edge-impact-bridge.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"
USER_NAME="${SUDO_USER:-$(whoami)}"
SENSOR_PORT="${EDGE_LAB_SENSOR_PORT:-/dev/ttyACM0}"
MATRIX_PORT="${EDGE_LAB_MATRIX_PORT:-/dev/ttyUSB0}"
HTTP_PORT="${EDGE_LAB_HTTP_PORT:-8088}"
HTTP_HOST="${EDGE_LAB_HOST:-127.0.0.1}"

if [[ ! -x "${ROOT_DIR}/.venv/bin/edge-impact-bridge" ]]; then
  echo "Missing virtualenv executable. Run scripts/jetson_prepare.sh first."
  exit 1
fi

sudo tee "${SERVICE_PATH}" >/dev/null <<SERVICE
[Unit]
Description=Edge Impact Lab bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${ROOT_DIR}
EnvironmentFile=-${ROOT_DIR}/.env.local
Environment=EDGE_LAB_SENSOR_PORT=${SENSOR_PORT}
Environment=EDGE_LAB_MATRIX_PORT=${MATRIX_PORT}
Environment=EDGE_LAB_HTTP_PORT=${HTTP_PORT}
Environment=EDGE_LAB_HOST=${HTTP_HOST}
ExecStart=${ROOT_DIR}/.venv/bin/edge-impact-bridge
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable --now "${SERVICE_NAME}"
sudo systemctl status "${SERVICE_NAME}" --no-pager
