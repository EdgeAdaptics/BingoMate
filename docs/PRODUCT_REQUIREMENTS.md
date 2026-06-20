# BingoMate Product Requirements

## MVP Scope

The first GitHub-ready version must prove the product shape end-to-end with safe simulated defaults:

- FastAPI backend serving health, chat, memory, skills, devices, voice turns, voice simulation, vision simulation, privacy-gated camera capture, and automation proposals.
- Local dashboard that works without a frontend build system.
- Full-screen boot display with animated Bingo character, local GIF avatar, startup chime, browser voice, and kiosk-mode Jetson autostart.
- SQLite memory for conversations, notes, preferences, routines, and learned knowledge.
- Runtime identity engine for Bingo's persona, privacy posture, system awareness, and user-approved growth signals.
- Context fusion engine that combines voice, vision, memory, devices, skills, events, identity, and privacy state.
- Skill registry with safe sample skills, persistent template skills, and a clear extension pattern.
- Device registry seeded with Jetson, ESP32 matrix, and Arduino Nano 33 BLE Sense.
- Permission-gated automation proposals.
- Industrial telemetry bridge retained as the first real-world device workflow.
- Documentation that explains product vision, architecture, UX, roadmap, security, and publishing.

## Experience Requirements

### Companion Home

- Shows assistant status, memory count, connected devices, active skills, and lab health.
- Shows Bingo's identity state, privacy posture, runtime platform, Jetson target, and optional load/temperature signals.
- Supports a text chat path before voice hardware is fully enabled.
- Supports a simulated voice-turn path before microphone capture is enabled.
- Makes it obvious when the system is in simulation mode.

### Boot Display

- Shows Bingo as an original animated 3D-style character on a connected display.
- Shows a local looping GIF avatar as a lightweight boot animation asset.
- Plays a local startup chime and browser voice when kiosk autoplay is enabled.
- Shows boot readiness for brain, memory, device trust, voice, and presence.
- Shows live identity, mode, device count, skill count, and proactive suggestions.
- Can start automatically on Jetson graphical boot.

### Memory Center

- Lists recent memories.
- Supports adding user-controlled notes.
- Supports search by text, tags, and local hash-vector retrieval.
- Supports user-controlled memory delete and export.
- Makes memory persistence explicit.

### Device Center

- Lists Jetson, ESP32, Arduino, and optional gateway devices.
- Shows connection type, role, and status.
- Separates simulated devices from physical devices.

### Skills Center

- Lists installed skills.
- Runs safe development skills.
- Supports user-created template skills without arbitrary code execution.
- Shows whether a skill requires approval before action.

### Automation Center

- Lets BingoMate propose an action.
- Blocks sensitive or physical actions until approved.
- Logs the proposal in a way that can later become an audit trail.
- Shows proactive suggestions from local context without executing them silently.

## Functional Requirements

| Area | Requirement | First Implementation |
| --- | --- | --- |
| Voice | Wake word, STT, dialogue, TTS | Simulated voice turns, local STT adapter boundary, and local WAV TTS adapter/fallback |
| Display | Always-on character GUI | Full-screen HTML/CSS kiosk display, local GIF avatar, startup chime, and browser voice |
| Vision | People, objects, gestures, scenes | Simulated scene endpoint, uploaded-image heuristics, and privacy-gated camera capture boundary |
| Reasoning | Local-first assistant reasoning | Local OpenAI-compatible/Ollama adapter, optional cloud assist, and deterministic fallback |
| Identity | System-aware Bingo persona and growth model | Local identity engine and dashboard card |
| Context | Multimodal and device-aware context fusion | Local context engine and proactive suggestions |
| Memory | Conversation, preference, episodic memory | SQLite store, text search, local hash-vector search, export, and delete |
| Skills | Extensible plugin-style capabilities | Python registry plus persistent template skill store |
| Devices | MQTT, BLE, REST, WebSocket-ready device model | Persistent local registry, signed REST intake, WebSocket events, MQTT dry-run/publish boundary, and BLE readiness status |
| Automation | Proactive suggestions and safe execution | Permission-gated proposals |
| Security | Local auth, encrypted local memory, secret hygiene, approval policy | Optional bearer token auth, encrypted memory fields, security policy, and docs |
| Dashboard | Local web UI | Static HTML/JS dashboard |
| Deployment | Jetson and PC runnable | Python package, scripts, Docker roadmap |

## API Requirements

- `GET /healthz` returns runtime health and simulation status.
- `GET /display` serves Bingo's boot display.
- `GET /api/voice/startup` and `/api/voice/startup.wav` provide startup voice text and local chime audio.
- `POST /api/voice/turn` runs a wake-word voice interaction from simulated text or local STT audio.
- `GET /api/voice/stt/status` reports local STT readiness.
- `POST /api/voice/transcribe` transcribes local audio or returns the simulation fallback.
- `GET/POST /api/voice/say.wav` returns local WAV audio for response playback.
- `GET /api/identity` returns Bingo's local identity, privacy posture, growth signals, and system awareness.
- `GET /api/context` returns fused local context signals and suggestions.
- `GET /api/assist/suggestions` returns proactive local suggestions only.
- `GET /api/reasoning/status` returns local LLM, cloud assist, and deterministic fallback readiness.
- `POST /api/reasoning/probe` runs a non-persistent reasoning runtime check.
- `GET /api/memories` lists recent or searched memories.
- `GET /api/memories/vector/status` reports local vector memory retrieval readiness.
- `GET /api/memories/search` searches memory with text, vector, or hybrid mode.
- `POST /api/memories` stores a user-controlled memory.
- `DELETE /api/memories/{memory_id}` deletes a user-controlled memory.
- `GET /api/memories/export` exports local memories.
- `POST /api/chat` records a chat turn and returns a contextual response.
- `GET /api/skills` lists available skills.
- `POST /api/skills` creates a local template skill.
- `POST /api/skills/{skill_name}/run` runs one skill.
- `DELETE /api/skills/{skill_name}` deletes a local template skill.
- `GET /api/devices` lists known devices.
- `POST /api/devices/register` registers a signed local device and persists device trust.
- `POST /api/devices/{device_id}/messages` accepts signed device messages.
- `GET /api/devices/transports` lists REST, WebSocket, MQTT, and BLE readiness.
- `POST /api/devices/mqtt/publish` builds a MQTT envelope and optionally publishes it when a broker is configured.
- `GET /api/events` and `WebSocket /ws/events` expose runtime events.
- `GET /api/vision/simulate` returns a scene understanding placeholder.
- `GET /api/vision/status` returns camera privacy/configuration state.
- `POST /api/vision/analyze` analyzes simulated scenes or uploaded images locally.
- `POST /api/vision/capture` attempts privacy-gated USB camera capture when explicitly enabled.
- `GET /api/voice/simulate` returns a wake-word transcript placeholder.
- `POST /api/automations/propose` returns or blocks an automation proposal.

## Acceptance Criteria

- `python -m compileall bingomate edge_lab scripts` succeeds.
- `python scripts/self_test.py` succeeds.
- `python scripts/preflight_publish.py` succeeds before GitHub push.
- `bingomate-api --host 127.0.0.1 --port 8090` starts the API and dashboard.
- `http://127.0.0.1:8090/display` renders the Bingo boot display.
- No secret appears in tracked files.
