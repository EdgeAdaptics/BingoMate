# Readiness Checks

Run the doctor before demos, before publishing, and after moving hardware between hosts.

```powershell
edge-impact-doctor --format markdown --out exports\doctor.md
```

Or without installing the package:

```powershell
python scripts\doctor.py --format markdown --out exports\doctor.md
```

## What It Checks

| Check | Purpose |
| --- | --- |
| `python` | Confirms Python is new enough for the bridge |
| `pyserial` | Confirms serial support is installed |
| `mqtt_optional` | Reports whether optional MQTT support is installed |
| `serial_ports` | Lists detected USB serial devices |
| `database` | Reports whether telemetry exists in SQLite |
| `publish_preflight` | Runs the local publish safety check |

Warnings do not block a local demo. Failures should be fixed before publishing or relying on the lab for a live hardware demo.

Use `docs/FIRMWARE_FLASHING.md` after serial ports appear but firmware behavior is not confirmed.

## Expected Current Windows Lab Evidence

The current host has shown:

| Device | Port | Meaning |
| --- | --- | --- |
| `COM3` | FTDI USB serial | Jetson serial console |
| `COM4` | CH9102 USB serial | ESP32 or serial board candidate |

## Jetson Evidence To Capture

After logging into the Jetson, run:

```bash
bash scripts/jetson_health.sh
edge-impact-doctor --format markdown --out exports/doctor-jetson.md
```

Attach `exports/doctor-jetson.md` to the case study or demo notes.
