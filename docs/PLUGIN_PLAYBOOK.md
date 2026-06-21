# Plugin Playbook

This repo is structured so the named plugins can contribute without forcing unnecessary work.

## NVIDIA

Use for Jetson-focused hardening:

- Validate Jetson service startup, serial devices, and `tegrastats`.
- Add future CUDA/TensorRT inference once a real model is chosen.
- Keep the current bridge light enough to run during hardware bring-up.

## Codex Security

Use after implementation changes:

- Scan secrets handling, serial command construction, service files, and dashboard endpoints.
- Confirm Wi-Fi credentials remain outside git.
- Review shell scripts before field use.

## OpenAI Developers

Use for optional AI-assisted operator workflows:

- Add an OpenAI-backed incident summarizer only after an API key is intentionally configured.
- Keep local telemetry and basic risk scoring functional without cloud dependency.

## Hugging Face

Use for edge ML upgrades:

- Train or evaluate a small anomaly model from collected SQLite telemetry.
- Export to ONNX or another Jetson-friendly runtime later.
- Keep the first version deterministic and explainable.

## Linear

Use when a team/project is available:

- Convert `docs/ROADMAP.md` into tracked issues.
- Keep hardware bring-up, showcase polish, and security hardening separated.

## Product Design

Use for dashboard polish:

- Product: industrial edge operations dashboard.
- Visual direction: restrained, dense, operations-first UI.
- Interactivity: fully functional live telemetry and history.

## Chrome And Computer Use

Use only when stateful browser or desktop interaction is required:

- Chrome for logged-in GitHub, dashboards, or web UIs that need browser state.
- Computer Use for Windows apps such as Arduino IDE if CLI upload is unavailable.
