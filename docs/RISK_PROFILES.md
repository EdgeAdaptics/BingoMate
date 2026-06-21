# Risk Profiles

Risk profiles let you tune `OK`, `WARN`, and `ALERT` behavior without editing code.

## Included Profiles

| File | Use |
| --- | --- |
| `configs/risk_profile.default.json` | Baseline thresholds used by the bridge |
| `configs/risk_profile.sensitive-demo.json` | More sensitive thresholds for short demos |

## Run With A Profile

```powershell
edge-impact-bridge --demo --risk-profile configs\risk_profile.sensitive-demo.json
```

Or on Jetson:

```bash
export EDGE_LAB_RISK_PROFILE=configs/risk_profile.default.json
edge-impact-bridge --sensor-port /dev/ttyACM0 --matrix-port /dev/ttyUSB0
```

## Seed Demo Data With A Profile

```powershell
edge-impact-seed-demo --db edge_lab.db --all --risk-profile configs\risk_profile.sensitive-demo.json
edge-impact-report --db edge_lab.db --format markdown --out exports\summary.md
```

## Fields

| Field | Meaning |
| --- | --- |
| `vibration_warn_g` | Vibration magnitude that adds warning risk |
| `vibration_alert_g` | Vibration magnitude that adds alert risk |
| `temperature_warn_c` | Temperature that adds warning risk |
| `temperature_alert_c` | Temperature that adds alert risk |
| `humidity_alert_pct` | Humidity that adds risk |
| `sound_alert_level` | Normalized sound level that adds risk |
| `warn_score` | Total score threshold for `WARN` |
| `alert_score` | Total score threshold for `ALERT` |

## Tuning Rule

Start conservative for unattended runs. Use the sensitive demo profile only when you need visible state changes during a short showcase.
