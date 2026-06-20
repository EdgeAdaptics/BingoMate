# Operations

## Local Demo Mode

```powershell
python -m pip install -e .
edge-impact-doctor --format markdown --out exports\doctor.md
edge-impact-bridge --demo --risk-profile configs\risk_profile.sensitive-demo.json
```

Open `http://127.0.0.1:8088`.

## Jetson Service Mode

```bash
export LAB_WIFI_SSID="simple_reuse"
export LAB_WIFI_PASSWORD="<do-not-commit>"
bash scripts/jetson_prepare.sh
bash scripts/install_systemd_service.sh
```

The installed service binds to `127.0.0.1` by default. Set `EDGE_LAB_HOST=0.0.0.0` before install only on a trusted lab network.

To publish to MQTT, put `EDGE_LAB_MQTT_HOST` and optional broker credentials in `.env.local` before starting the service. See `docs/MQTT_INTEGRATION.md`.

To tune scoring, set `EDGE_LAB_RISK_PROFILE` to one of the JSON files in `configs/`. See `docs/RISK_PROFILES.md`.

Check service health:

```bash
systemctl status edge-impact-bridge --no-pager
curl http://127.0.0.1:8088/healthz
curl http://127.0.0.1:8088/metrics
edge-impact-doctor --format markdown --out exports/doctor.md
```

See `docs/OBSERVABILITY.md` for Prometheus scrape configuration.

## Recovery Checklist

- If the Jetson is unreachable on Wi-Fi, use the serial console on `COM3`.
- If the matrix does not update, confirm the ESP32 serial port and I2C addresses.
- If Arduino telemetry is missing, check whether it enumerates as `/dev/ttyACM0` on Jetson.
- If the dashboard is empty, run `edge-impact-bridge --demo` to isolate software from hardware.
