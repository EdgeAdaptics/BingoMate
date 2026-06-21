#!/usr/bin/env bash
set -euo pipefail

PORT="${BINGOMATE_PORT:-8090}"
DISPLAY_URL="${BINGOMATE_DISPLAY_URL:-http://127.0.0.1:${PORT}/display}"
HEALTH_URL="${BINGOMATE_HEALTH_URL:-http://127.0.0.1:${PORT}/healthz}"

if [[ -n "${BINGOMATE_DISPLAY_TOKEN:-}" ]]; then
  DISPLAY_URL="${DISPLAY_URL}#token=${BINGOMATE_DISPLAY_TOKEN}"
fi

health_ready() {
  if command -v curl >/dev/null 2>&1 && curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    HEALTH_URL="${HEALTH_URL}" python3 - <<'PY'
import os
import sys
import urllib.request

try:
    with urllib.request.urlopen(os.environ["HEALTH_URL"], timeout=2) as response:
        sys.exit(0 if response.status == 200 else 1)
except Exception:
    sys.exit(1)
PY
  fi
  return 1
}

READY=0
for _ in $(seq 1 90); do
  if health_ready; then
    READY=1
    break
  fi
  sleep 1
done

if [[ "${READY}" != "1" ]]; then
  echo "BingoMate API did not become healthy at ${HEALTH_URL}."
  exit 1
fi

BROWSER=""
for candidate in chromium-browser chromium google-chrome-stable google-chrome; do
  if command -v "${candidate}" >/dev/null 2>&1; then
    BROWSER="${candidate}"
    break
  fi
done

if [[ -z "${BROWSER}" ]]; then
  echo "No Chromium-compatible browser found. Install chromium-browser or chromium."
  exit 1
fi

exec "${BROWSER}" \
  --kiosk \
  --autoplay-policy=no-user-gesture-required \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 \
  "${DISPLAY_URL}"
