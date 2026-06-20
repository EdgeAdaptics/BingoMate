# Linear Backlog Draft

Use this when a Linear workspace, team, and project are selected.

## Project

Name: `Edge Impact Lab`

Description: Portable Jetson Orin Nano industrial IoT lab for predictive maintenance, physical status display, and edge AI growth.

## Issues

| Title | Priority | Labels | Acceptance Criteria |
| --- | --- | --- | --- |
| Confirm Jetson serial login and Wi-Fi | High | hardware, jetson | Jetson joins `simple_reuse`; IP address recorded; no password committed |
| Flash Arduino telemetry firmware | High | hardware, firmware | Nano 33 BLE Sense emits valid JSON once per second |
| Flash ESP32 matrix firmware | High | hardware, firmware | Matrix responds to `STATUS:OK`, `STATUS:WARN`, and `STATUS:ALERT` |
| Run bridge on Jetson | High | edge, jetson | Dashboard health endpoint returns `ok`; readings are stored in SQLite |
| Capture showcase screenshots | Medium | portfolio | Dashboard and matrix images are added to docs |
| Add MQTT publisher | Medium | industrial-iot | Readings publish to local broker with reconnect handling |
| Add model training notebook | Medium | edge-ai | Telemetry export trains or evaluates an anomaly detector |
| Harden systemd service | Medium | security | Service runs as dedicated user with documented hardware permissions |
| Publish GitHub repository | High | portfolio | Repo exists under `EdgeAdaptics`; initial commit pushed |
