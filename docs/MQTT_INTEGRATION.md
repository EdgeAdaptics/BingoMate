# MQTT Integration

MQTT publishing is optional. The bridge keeps collecting telemetry, updating the dashboard, and driving the matrix when no broker is configured.

## Install Optional Support

```bash
python -m pip install -e ".[mqtt]"
```

## Run With A Broker

```bash
edge-impact-bridge \
  --sensor-port /dev/ttyACM0 \
  --matrix-port /dev/ttyUSB0 \
  --mqtt-host 127.0.0.1 \
  --mqtt-topic edge-impact-lab
```

The bridge publishes:

| Topic | Payload |
| --- | --- |
| `edge-impact-lab/readings` | JSON reading with `schema`, `ts`, `source`, `payload`, `risk`, `status`, and `reasons` |
| `edge-impact-lab/status` | Retained text status: `OK`, `WARN`, or `ALERT` |

## Credentials

Use environment variables instead of command history when credentials are needed:

```bash
export EDGE_LAB_MQTT_HOST="broker.local"
export EDGE_LAB_MQTT_USERNAME="edge-lab"
export EDGE_LAB_MQTT_PASSWORD="<do-not-commit>"
edge-impact-bridge --sensor-port /dev/ttyACM0 --matrix-port /dev/ttyUSB0
```

Do not commit broker passwords or cloud connection strings.

For systemd service mode, put broker settings in `.env.local` on the Jetson:

```bash
EDGE_LAB_MQTT_HOST=broker.local
EDGE_LAB_MQTT_USERNAME=edge-lab
EDGE_LAB_MQTT_PASSWORD=<do-not-commit>
```

`scripts/install_systemd_service.sh` reads `.env.local` through `EnvironmentFile`, and `.gitignore` keeps it out of git.

## Local Test Subscriber

With a local broker running:

```bash
mosquitto_sub -h 127.0.0.1 -t 'edge-impact-lab/#' -v
```

Then run:

```bash
edge-impact-bridge --demo --mqtt-host 127.0.0.1
```
