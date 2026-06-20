# Project Goal

Build BingoMate, a credible futuristic AI companion and industrial edge computing showcase around the Jetson Orin Nano Super Developer Kit.

## Outcome

BingoMate should be useful for personal productivity, professional field work, learning, interviews, GitHub portfolio review, and future edge AI demos. It should show:

- A local AI companion with voice, vision, memory, reasoning, skills, and automation.
- Sensor telemetry ingestion from Arduino Nano 33 BLE Sense.
- Local edge decisioning on the Jetson.
- Physical status display through ESP32 and a 4x 8x8 I2C LED matrix.
- A local dashboard for conversations, memory, devices, automations, health, and telemetry.
- Clean setup scripts that can be repeated without leaking credentials.
- A roadmap toward local LLMs, multimodal perception, secure device identity, predictive maintenance, and fleet operations.

## First Showcase: BingoMate Edge Companion

An offline-first assistant running on Jetson:

1. User opens the local BingoMate dashboard and asks for a lab readiness summary.
2. BingoMate recalls stored preferences and recent device state from SQLite.
3. Jetson combines simulated voice, vision, memory, and sensor context.
4. BingoMate proposes a safe next action, such as checking firmware or preparing a demo script.
5. User-approved automations can update the ESP32 matrix, log reminders, or trigger lab workflows.

## Physical Showcase: Industrial Edge Microcell

1. Arduino streams temperature, humidity, accelerometer, and sound metrics.
2. Jetson scores each reading into `OK`, `WARN`, or `ALERT`.
3. ESP32 matrix displays live status and risk bar.
4. Jetson dashboard shows latest telemetry and recent history.
5. Local SQLite storage preserves readings for offline analysis.

## Career Signal

This project is designed to demonstrate practical competence in:

- Jetson Linux bring-up.
- Serial and USB hardware integration.
- FastAPI service architecture.
- AI product design and edge-native system design.
- Local-first memory and privacy architecture.
- Plugin and device framework design.
- Edge gateway software design.
- Industrial telemetry modeling.
- Secure secrets handling.
- Deployable services on embedded Linux.
