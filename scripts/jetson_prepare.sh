#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSID="${LAB_WIFI_SSID:-simple_reuse}"
PASSWORD="${LAB_WIFI_PASSWORD:-}"

echo "== Edge Impact Lab Jetson prepare =="
echo "Repo: ${ROOT_DIR}"

if command -v nmcli >/dev/null 2>&1; then
  if [[ -n "${PASSWORD}" ]]; then
    echo "Configuring Wi-Fi profile for ${SSID}"
    sudo nmcli radio wifi on || true
    sudo nmcli dev wifi connect "${SSID}" password "${PASSWORD}" || \
      sudo nmcli con up "${SSID}" || true
  else
    echo "LAB_WIFI_PASSWORD is empty; skipping Wi-Fi configuration."
  fi
else
  echo "nmcli not found; skipping Wi-Fi configuration."
fi

echo "Installing Python environment"
python3 -m venv "${ROOT_DIR}/.venv"
source "${ROOT_DIR}/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e "${ROOT_DIR}"

if [ "${INSTALL_CODEX_CLI:-0}" = "1" ]; then
  bash "${ROOT_DIR}/scripts/jetson_install_codex_cli.sh"
fi

echo "Serial devices:"
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true

echo "I2C buses:"
ls -l /dev/i2c-* 2>/dev/null || true

echo "NVIDIA status:"
if command -v tegrastats >/dev/null 2>&1; then
  timeout 3s tegrastats || true
else
  echo "tegrastats not found."
fi

echo "Done. Start with:"
echo "source .venv/bin/activate"
echo "bingomate-api --host 0.0.0.0 --port 8090"
echo "Open Bingo display at http://127.0.0.1:8090/display"
echo "Install boot display with: bash scripts/install_bingomate_display_service.sh"
echo "edge-impact-bridge --sensor-port /dev/ttyACM0 --matrix-port /dev/ttyUSB0"
echo "Use EDGE_LAB_HOST=0.0.0.0 only on a trusted lab network."
