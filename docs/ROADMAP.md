# Roadmap

This roadmap now tracks BingoMate as the primary product and the Edge Impact Lab as its first physical-world showcase.

## Milestone 0: Product Design And Scaffold

- Define the product vision, requirements, architecture, UX system, and technical roadmap.
- Package the FastAPI backend and dashboard.
- Keep the first scaffold offline-first and simulation-capable.
- Validate the repo before publishing.

## Milestone 1: Repeatable Hardware Bring-Up

- Confirm Jetson login credentials and configure Wi-Fi over serial.
- Flash ESP32 matrix firmware and verify `STATUS:*` messages.
- Flash Arduino sensor firmware and verify JSON telemetry.
- Run `edge-impact-bridge` on Jetson with both serial devices.
- Install Codex CLI on Jetson when authentication is available.

## Milestone 2: BingoMate Companion Demo

- Run `bingomate-api` on Jetson.
- Show local memory, chat, skills, devices, and automation proposals.
- Demonstrate that sensitive actions are blocked until approved.
- Add screenshots of the dashboard and one short product walkthrough.

## Milestone 3: Industrial Edge Demo

- Add a short demo script that explains the predictive maintenance story.
- Record normal, warning, and alert telemetry examples.
- Add screenshots of the dashboard and matrix output.
- Publish the repo under `EdgeAdaptics`.

## Milestone 4: Industrial Edge Depth

- Add device identity and signed telemetry.
- Use the MQTT publisher with a local broker and optional cloud bridge.
- Add model training from collected telemetry.
- Add fleet-style systemd health checks and log rotation.
- Scrape `/metrics` into Prometheus or another lab monitoring stack.
- Calibrate risk profiles from real collected telemetry.

## Milestone 5: Career Portfolio

- Add architecture diagram and one-page case study.
- Add a demo video link.
- Add resume bullet points tied to measurable outcomes.
- Create GitHub issues or Linear tickets for future work.
