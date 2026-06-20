# BingoMate Technical Roadmap

## Phase 0: GitHub-Ready Product Scaffold

- Package the FastAPI backend as `bingomate-api`.
- Serve a local dashboard from `apps/dashboard`.
- Serve a full-screen boot display from `apps/bingo_display` with a local GIF avatar, startup chime, and browser voice.
- Keep all hardware paths simulation-capable.
- Preserve the Edge Impact Lab as the first physical workflow.
- Pass compile, self-test, and publish preflight checks.

## Phase 1: Jetson Bring-Up

- Configure Jetson Wi-Fi and SSH after user login is available.
- Install system packages, Python environment, and systemd service.
- Run `bingomate-api` locally on Jetson.
- Run `edge-impact-bridge` with Arduino and ESP32 serial devices.
- Add Codex CLI on Jetson for local assisted development when credentials are available.

## Phase 2: Voice Companion

- Use `/api/voice/turn` as the first end-to-end voice interaction contract.
- Use `/api/voice/say.wav` for local response playback through `espeak-ng`/`espeak` or the offline prosody fallback.
- Use `/api/voice/stt/status` and `/api/voice/transcribe` as the local STT adapter boundary.
- Add wake-word boundary and microphone capture.
- Add direct microphone capture and streaming VAD.
- Add Jetson-accelerated local STT and higher-quality local TTS models.
- Add push-to-talk fallback for noisy lab environments.
- Add audio health checks and speaker test commands.
- Upgrade boot display speech from browser synthesis to local TTS once the Jetson voice stack is installed.

## Phase 3: Vision Companion

- Use `/api/vision/status`, `/api/vision/analyze`, and `/api/vision/capture` as the first local vision contract.
- Keep USB camera capture privacy-gated through `BINGOMATE_CAMERA_ENABLED` plus request-level approval.
- Add people/object/gesture/scene inference adapter.
- Add low-frame-rate context mode for power efficiency.
- Add privacy shutter and visual recording indicators.
- Feed real scene observations into the context engine after camera privacy controls are active.

## Phase 4: Memory And Learning

- Add preference, routine, episodic, and learned-knowledge memory types.
- Expand the Bingo identity engine with user-approved persona preferences, feedback summaries, and hardware-aware state transitions.
- Expand proactive suggestions with routines, reminders, field checklists, and user feedback.
- Add memory review, delete, export, and retention controls.
- Add OS keyring or Jetson fTPM-backed key wrapping for encrypted memory keys.
- Add optional embeddings and vector search.
- Add feedback loops for skill quality and assistant behavior.

## Phase 5: Device And Automation Ecosystem

- Add MQTT broker integration for ESP32 and external IoT nodes.
- Add BLE integration for wearable and mobile sensor nodes.
- Add signed device registration and trust-on-first-use flow.
- Add device key rotation and stronger trust-on-first-use approval UX.
- Add signed skill package import with permission scopes.

## Phase 6: Native Performance Path

- Move hot camera/audio loops to C++ where Python becomes a bottleneck.
- Add TensorRT-compatible model adapters behind stable interfaces.
- Use Rust for long-running secure device and identity services if needed.
- Add Docker profiles for PC development and Jetson deployment.

## Phase 7: Public Showcase

- Publish the repository under EdgeAdaptics.
- Add screenshots, demo video, and one-page case study.
- Open tracked GitHub issues for milestones.
- Package a repeatable demo: personal assistant workflow plus industrial microcell workflow.
