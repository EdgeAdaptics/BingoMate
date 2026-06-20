#!/usr/bin/env bash
set -euo pipefail

echo "== Host =="
hostnamectl 2>/dev/null || hostname

echo "== Network =="
ip -brief addr || true
nmcli -t -f active,ssid,device dev wifi 2>/dev/null | grep '^yes' || true

echo "== Serial =="
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true

echo "== I2C =="
ls -l /dev/i2c-* 2>/dev/null || true

echo "== NVIDIA =="
cat /etc/nv_tegra_release 2>/dev/null || true
if command -v tegrastats >/dev/null 2>&1; then
  timeout 3s tegrastats || true
fi

echo "== Service =="
systemctl status edge-impact-bridge --no-pager 2>/dev/null || true
