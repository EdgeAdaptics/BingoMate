# Hardware Bring-Up Notes

## Known Connections

| Component | Expected Role | Current Host Port |
| --- | --- | --- |
| Jetson Orin Nano Super serial console | Linux console and Wi-Fi recovery | `COM3` |
| ESP32 CH9102 board | LED matrix controller candidate | `COM4` |
| Arduino Nano 33 BLE Sense | Sensor telemetry over USB | Check with `edge-impact-inventory --probe` |

## Jetson Serial Console

The serial console currently prints:

```text
karguzedge login:
```

Wi-Fi can be configured after logging in:

```powershell
$env:LAB_WIFI_SSID="simple_reuse"
$env:LAB_WIFI_PASSWORD="<do-not-commit>"
python scripts\connect_jetson_wifi_serial.py --port COM3
```

## ESP32 Matrix

The ESP32 sketch expects four HT16K33-compatible 8x8 matrix backpacks on I2C addresses:

```text
0x70, 0x71, 0x72, 0x73
```

It accepts serial lines from the Jetson:

```text
STATUS:OK:10
STATUS:WARN:42
STATUS:ALERT:88
```

## Arduino Sensor Node

The Arduino sketch emits one JSON line per second:

```json
{"temperature_c":31.25,"humidity_pct":55.20,"ax":0.010,"ay":0.020,"az":1.004,"sound_level":0.123}
```

Use this command to identify the port:

```powershell
python scripts\inventory_serial.py --probe
```

See `docs/FIRMWARE_FLASHING.md` for reproducible compile and upload commands.
