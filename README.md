# BingoMate

BingoMate is an open-source, privacy-first, offline-capable AI companion for the NVIDIA Jetson Orin Nano Super. It is the foundation of the EdgeAdaptics NAEAI ecosystem: a local assistant that can see, hear, speak, remember, reason, learn skills, operate devices, and help with real-world work while keeping personal data local by default.

The repo also includes the original Edge Impact Lab industrial IoT bridge for the Jetson, Arduino Nano 33 BLE Sense, ESP32, and 4x 8x8 I2C LED matrix. That lab becomes BingoMate's first physical sensing and automation layer.

## Product Direction

- **AI companion:** wake word, voice conversation, local reasoning, memory, camera perception, and proactive assistance.
- **Character display:** full-screen animated Bingo GUI with local boot GIF, startup chime, browser voice, and Jetson kiosk boot path.
- **Edge-native:** Jetson-first runtime with simulated development paths when hardware is disconnected.
- **Privacy-first:** local SQLite memory, local dashboard, permission-gated actions, and no committed secrets.
- **Extensible:** plugin-style skills, devices, automation policies, REST APIs, and future MQTT/BLE/WebSocket bridges.
- **Portfolio-ready:** architecture docs, roadmap, dashboard scaffold, hardware firmware, tests, CI, and publish guidance.

See `docs/PRODUCT_VISION.md`, `docs/PRODUCT_REQUIREMENTS.md`, `docs/BINGOMATE_ARCHITECTURE.md`, `docs/UX_DESIGN_SYSTEM.md`, `docs/CHARACTER_DESIGN.md`, `docs/BOOT_DISPLAY.md`, `docs/MEMORY_MODEL.md`, `docs/SECURITY_MODEL.md`, `docs/API_CONTRACT.md`, `docs/BINGOMATE_SETUP.md`, and `docs/TECHNICAL_ROADMAP.md` for the end-to-end product design.

## BingoMate Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
bingomate-api --host 127.0.0.1 --port 8090
```

Open BingoMate at `http://127.0.0.1:8090`.
Open the full-screen Bingo boot display at `http://127.0.0.1:8090/display`. It shows the 3D-style Bingo GUI, local GIF avatar, boot sequence, startup chime, and browser voice when kiosk autoplay is enabled.

Useful API checks:

```powershell
curl http://127.0.0.1:8090/healthz
curl http://127.0.0.1:8090/api/reasoning/status
curl http://127.0.0.1:8090/api/memories/vector/status
curl "http://127.0.0.1:8090/api/memories/search?q=privacy%20workflow&mode=hybrid"
curl http://127.0.0.1:8090/api/devices
curl http://127.0.0.1:8090/api/devices/transports
curl -X POST http://127.0.0.1:8090/api/chat -H "Content-Type: application/json" -d "{\"prompt\":\"Help me prepare the Jetson lab demo\"}"
curl -X POST http://127.0.0.1:8090/api/reasoning/probe -H "Content-Type: application/json" -d "{\"prompt\":\"Confirm reasoning runtime\",\"include_memories\":false}"
curl http://127.0.0.1:8090/api/voice/stt/status
curl -X POST http://127.0.0.1:8090/api/voice/transcribe -H "Content-Type: application/json" -d "{\"audio_hint\":\"hey bingo status\"}"
curl -X POST http://127.0.0.1:8090/api/voice/turn -H "Content-Type: application/json" -d "{\"audio_hint\":\"hey bingo summarize my lab readiness\"}"
curl -X POST http://127.0.0.1:8090/api/vision/analyze -H "Content-Type: application/json" -d "{\"scene\":\"jetson lab desk\"}"
curl -X POST http://127.0.0.1:8090/api/devices/mqtt/publish -H "Content-Type: application/json" -d "{\"device_id\":\"esp32-matrix\",\"payload\":{\"status\":\"OK\"},\"dry_run\":true}"
```

## Edge Impact Lab Quick Start

The industrial telemetry bridge remains available for hardware demos:

## Current Lab Discovery

Detected from this Windows host:

| Device | Port | Evidence |
| --- | --- | --- |
| Jetson serial console | `COM3` | FTDI USB serial, login prompt `karguzedge login:` |
| ESP32 or CH9102 serial board | `COM4` | CH9102 USB serial |

The Jetson serial console is reachable, but Wi-Fi setup over serial requires a Jetson username/password login.

```powershell
python scripts\inventory_serial.py --probe
edge-impact-doctor --format markdown --out exports\doctor.md
edge-impact-bridge --demo --matrix-port COM4
```

Open the dashboard at `http://127.0.0.1:8088`.

Seed deterministic showcase telemetry when hardware is disconnected:

```powershell
edge-impact-seed-demo --db edge_lab.db --all
```

Export collected telemetry for analysis or model training:

```powershell
edge-impact-export --db edge_lab.db --format csv --out exports\readings.csv
edge-impact-export --db edge_lab.db --format jsonl --out exports\readings.jsonl
```

Generate a maintenance-style summary:

```powershell
edge-impact-report --db edge_lab.db --format markdown --out exports\summary.md
```

Publish telemetry to a local MQTT broker when needed:

```powershell
python -m pip install -e ".[mqtt]"
edge-impact-bridge --demo --mqtt-host 127.0.0.1 --mqtt-topic edge-impact-lab
```

Tune risk thresholds for demos or assets:

```powershell
edge-impact-bridge --demo --risk-profile configs\risk_profile.sensitive-demo.json
```

Monitor the bridge:

```powershell
curl http://127.0.0.1:8088/healthz
curl http://127.0.0.1:8088/metrics
```

## Quick Start On Jetson

After logging into the Jetson:

```bash
git clone https://github.com/EdgeAdaptics/BingoMate.git
cd BingoMate
export LAB_WIFI_SSID="simple_reuse"
export LAB_WIFI_PASSWORD="your-lab-password"
bash scripts/jetson_prepare.sh
source .venv/bin/activate
edge-impact-bridge --sensor-port /dev/ttyACM0 --matrix-port /dev/ttyUSB0
```

To boot directly into Bingo's animated character display on an attached Jetson monitor:

```bash
bash scripts/install_bingomate_display_service.sh
```

Do not commit `.env`, `.env.local`, Wi-Fi passwords, tokens, or SSH keys.

## Showcase Story

This lab demonstrates a practical edge AI/IIoT pattern: noisy physical telemetry is collected near the machine, converted into local status and risk signals, displayed on a rugged low-power matrix, and logged locally for auditability. It is intentionally small enough to carry into a lab interview or demo, but structured like an industrial edge gateway.

See `docs/SHOWCASE.md` for the portfolio narrative, `docs/DEMO_RUNBOOK.md` for demo steps, `docs/FIRMWARE_FLASHING.md` for firmware upload, `docs/READINESS_CHECKS.md` for lab health checks, `docs/OBSERVABILITY.md` for health and metrics, `docs/RISK_PROFILES.md` for threshold tuning, `docs/CASE_STUDY_WORKFLOW.md` for post-demo evidence, `docs/MQTT_INTEGRATION.md` for industrial broker integration, `docs/ROADMAP.md` for the staged plan, `docs/AI_EDGE_UPGRADES.md` for the AI path, `docs/LINEAR_BACKLOG.md` for planning, and `docs/GITHUB_PUBLISH.md` for publishing.

## Repository Layout

```text
bingomate/                        FastAPI backend, memory, skills, devices, reasoning
apps/dashboard/                   Offline-first local web dashboard
apps/bingo_display/               Full-screen animated Bingo character display and local boot GIF
edge_lab/                         Python bridge and dashboard
firmware/arduino_nano33_ble_sense Arduino sensor sketch
firmware/esp32_matrix_status      ESP32 matrix sketch
scripts/                          Bring-up and health scripts
configs/                          Non-secret lab defaults
docs/                             Goal, hardware, and operating notes
deploy/                           Docker and deployment assets
```

## Next Physical Step

Log into the Jetson serial console on `COM3`, then run:

```powershell
$env:LAB_WIFI_SSID="simple_reuse"
$env:LAB_WIFI_PASSWORD="<do-not-commit>"
python scripts\connect_jetson_wifi_serial.py --port COM3
```
