# AI And Edge Upgrade Path

The first version is deterministic and local-first. Add AI only when the hardware stream is stable and there is enough collected telemetry to evaluate it.

## Hugging Face Path

Use collected SQLite telemetry to train or evaluate a small anomaly detector:

- Export readings from `edge_lab.db`.
- Use `edge-impact-export --format jsonl` to create a training-friendly dataset.
- Use `edge-impact-report` to compare model results against rule-based operational summaries.
- Train a lightweight vibration and sound anomaly model.
- Convert to ONNX or another Jetson-friendly runtime.
- Compare model output against the current rule-based `OK`, `WARN`, and `ALERT` score.

## NVIDIA Jetson Path

Use Jetson acceleration after there is a real model target:

- Keep the bridge service running independently from inference.
- Add a separate inference worker process.
- Track `tegrastats` during demos to show edge resource awareness.
- Add camera inspection later only after the serial telemetry demo is stable.

## OpenAI Developers Path

Use OpenAI only for operator assistance, not core safety decisions:

- Summarize recent events into a maintenance note.
- Generate incident reports from local telemetry windows.
- Explain why a reading is `WARN` or `ALERT` in technician-friendly language.
- Keep the API key in `.env.local` or the platform key setup flow, never in source control.

## Rule

Cloud AI can explain and summarize. The Jetson should keep collecting, scoring, displaying, and storing telemetry even when the internet is unavailable.
