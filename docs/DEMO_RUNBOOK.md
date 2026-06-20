# Demo Runbook

Use this when showing the lab to a reviewer, hiring manager, teammate, or customer.

## Five-Minute Version

1. Start the bridge:

   ```powershell
   edge-impact-doctor --format markdown --out exports\doctor.md
   edge-impact-bridge --demo --risk-profile configs\risk_profile.sensitive-demo.json
   ```

2. Open `http://127.0.0.1:8088`.
3. Explain that the dashboard is running locally and does not need cloud access.
4. Show health and metrics:

   ```powershell
   curl http://127.0.0.1:8088/healthz
   curl http://127.0.0.1:8088/metrics
   ```

5. Export telemetry:

   ```powershell
   edge-impact-export --db edge_lab.db --format csv --out exports\demo.csv
   edge-impact-report --db edge_lab.db --format markdown --out exports\summary.md
   ```

6. Optional broker demo:

   ```powershell
   edge-impact-bridge --demo --mqtt-host 127.0.0.1
   ```

7. Show `docs/SHOWCASE.md` and the architecture diagram.

## Hardware Version

1. Confirm serial devices:

   ```powershell
   python scripts\inventory_serial.py --probe
   ```

2. Flash the Arduino sketch in `firmware/arduino_nano33_ble_sense`.
3. Flash the ESP32 sketch in `firmware/esp32_matrix_status`.
   Use `docs/FIRMWARE_FLASHING.md` for reproducible CLI commands.
4. Start the Jetson bridge with real ports:

   ```bash
   edge-impact-bridge --sensor-port /dev/ttyACM0 --matrix-port /dev/ttyUSB0 --host 127.0.0.1
   ```

5. Move, tap, warm, or cool the Arduino sensor node and watch status change.

## Offline Fallback

If hardware is not streaming, seed deterministic data:

```powershell
edge-impact-seed-demo --db edge_lab.db --all --risk-profile configs\risk_profile.sensitive-demo.json
edge-impact-export --db edge_lab.db --format jsonl --out exports\seeded.jsonl
```

Then start:

```powershell
edge-impact-bridge --demo
```

## Talking Points

- The Jetson acts as an edge gateway, not just a development board.
- The status display is physical and local, useful when a browser is not open.
- SQLite creates an audit trail for later root-cause analysis.
- The current scoring is explainable; the AI roadmap can replace or augment it after real data is collected.
- Secrets and Wi-Fi credentials are kept out of source control.

## Evidence To Capture

- Dashboard screenshot showing `OK`, `WARN`, and `ALERT`.
- Photo of the 32x8 matrix status display.
- CSV or JSONL export sample.
- Jetson `scripts/jetson_health.sh` output.
- Short video showing sensor motion changing status.
