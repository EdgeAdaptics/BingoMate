# BingoMate API Contract

## Base URL

Local development:

```text
http://127.0.0.1:8090
```

## Display Surfaces

`GET /`

Serves the local dashboard from `apps/dashboard`.

`GET /display`

Serves Bingo's full-screen boot display from `apps/bingo_display`.

`GET /display/assets/bingo-boot.gif`

Serves the local looping Bingo boot avatar used by the kiosk display.

## Health

`GET /healthz`

Returns assistant name, simulation state, memory database path, device trust database path, and camera enablement state.
It also reports whether optional cloud assist, local auth, memory encryption, and device trust encryption are enabled.

`GET /api/auth/status`

Returns whether local API authentication is required. When `BINGOMATE_AUTH_TOKEN` is set, protected API calls must send one of:

```text
Authorization: Bearer <token>
X-BingoMate-Token: <token>
```

`GET /api/security/status`

Returns local auth, memory encryption, and device trust encryption status.

`GET /api/identity`

Returns Bingo's local identity profile, privacy posture, user-approved growth signals, and system awareness snapshot. This endpoint is protected when `BINGOMATE_AUTH_TOKEN` is enabled because it exposes local runtime and device metadata.

```json
{
  "schema": "bingomate-identity/v1",
  "name": "Bingo",
  "state": "learning",
  "privacy_posture": {
    "mode": "local-plain-storage"
  },
  "system_awareness": {
    "target_brain": "NVIDIA Jetson Orin Nano Super",
    "device_count": 3,
    "skill_count": 2
  }
}
```

## Memories

`GET /api/memories?q=&limit=20`

Lists recent memories or text search results.

`GET /api/memories/vector/status`

Reports the local vector retrieval mode. The current implementation computes hash vectors in memory from local SQLite rows, persists no vector values, and calls no external embedding service.

`GET /api/memories/search?q=&mode=hybrid&limit=20`

Searches memory with `text`, `vector`, or `hybrid` retrieval. Hybrid mode combines local hash-vector similarity, token overlap, importance, tags, and recency.

```json
{
  "schema": "bingomate-memory-search/v1",
  "query": "privacy workflow",
  "mode": "hybrid",
  "results": [
    {
      "score": 0.82,
      "reasons": ["vector_similarity", "token_overlap"],
      "memory": {
        "kind": "preference",
        "content": "Prefer local-first workflows"
      }
    }
  ]
}
```

`POST /api/memories`

```json
{
  "kind": "preference",
  "content": "Prefer local-first workflows",
  "importance": 8,
  "tags": ["privacy"],
  "metadata": {}
}
```

`DELETE /api/memories/{memory_id}`

Deletes a user-controlled memory record.

`GET /api/memories/export?format=jsonl`

Exports all memories. Supported formats are `jsonl`, `json`, and `csv`.

## Chat

`POST /api/chat`

```json
{
  "prompt": "Help me prepare the Jetson demo",
  "remember": true
}
```

BingoMate tries configured local LLMs first, optional OpenAI cloud assist second, and deterministic local fallback last. Chat records conversation turns when `remember` is true.

`GET /api/reasoning/status`

Returns the active reasoning order and configuration state without calling the model server.

```json
{
  "schema": "bingomate-reasoning-status/v1",
  "default_mode": "local-simulation",
  "active_order": ["local_llm", "cloud_assist", "deterministic_fallback"],
  "local_llm": {
    "enabled": false,
    "configured": false,
    "provider": "openai-compatible"
  }
}
```

`POST /api/reasoning/probe`

Runs a non-persistent reasoning check. This is useful for dashboard validation after starting a local llama.cpp, vLLM, or Ollama server.

```json
{
  "prompt": "Summarize BingoMate reasoning runtime in one sentence.",
  "include_memories": false
}
```

## Skills

`GET /api/skills`

Lists registered skills.

`POST /api/skills`

Creates a safe local template skill. Template skills do not execute arbitrary code. They replace `{prompt}` and `{context}` placeholders and return a drafted result.

```json
{
  "name": "daily_lab_brief",
  "description": "Drafts a local Jetson lab briefing.",
  "template": "Prepare a lab brief for: {prompt}. Context: {context}",
  "requires_approval": true
}
```

`POST /api/skills/{skill_name}/run`

```json
{
  "prompt": "Draft a reminder",
  "context": {}
}
```

`DELETE /api/skills/{skill_name}`

Deletes a local template skill. Built-in skills cannot be deleted through this endpoint.

## Devices

`GET /api/devices`

Lists known devices including Jetson, ESP32, and Arduino simulated records.

`POST /api/devices/register`

Registers a local or lab device with a shared secret for signed REST/MQTT-style messages.
BingoMate derives a local HMAC key from the shared secret and persists registered device trust in `BINGOMATE_DEVICES_DB`. When `BINGOMATE_DEVICE_KEY` is set, the derived HMAC keys are encrypted at rest.
Sensitive metadata keys such as passwords, tokens, credentials, and private keys are redacted before persistence.

```json
{
  "device_id": "esp32-matrix-01",
  "name": "ESP32 Matrix Node",
  "kind": "automation_node",
  "role": "Status display",
  "transport": "mqtt",
  "shared_secret": "<local-shared-secret>",
  "metadata": {
    "location": "lab"
  }
}
```

`POST /api/devices/{device_id}/messages`

Accepts a signed device message. The signature is HMAC-SHA256 over BingoMate's canonical device message body.
Replay nonces are persisted so a signed message cannot be replayed after an API restart.

```json
{
  "timestamp": 1781946000.0,
  "nonce": "unique-message-id",
  "payload": {
    "temperature_c": 24.2
  },
  "signature": "<hex-hmac-sha256>"
}
```

Rejected signatures, unknown devices, stale timestamps, and replayed nonces return `401`.

`GET /api/devices/transports`

Returns device transport readiness for REST, WebSocket, MQTT, and BLE. MQTT and BLE dependencies are optional so the endpoint can show whether the runtime is configured before physical hardware is attached.

```json
{
  "schema": "bingomate-device-transports/v1",
  "transports": [
    {
      "name": "mqtt",
      "enabled": false,
      "available": false,
      "configured": false,
      "details": {
        "host": "not configured",
        "port": 1883,
        "topic": "bingomate/devices"
      }
    }
  ]
}
```

`POST /api/devices/mqtt/publish`

Builds and optionally publishes a BingoMate MQTT envelope for a registered device. `dry_run` defaults to `true`, which is useful for demos and dashboard checks without a broker.

```json
{
  "device_id": "esp32-matrix",
  "payload": {
    "status": "OK",
    "source": "dashboard-dry-run"
  },
  "dry_run": true
}
```

When `dry_run` is `false`, set `BINGOMATE_MQTT_HOST` and install `bingomate-edge[mqtt]`.
Publish topics are bounded to 256 characters and reject MQTT wildcard characters (`+`, `#`) and null bytes.

## Events

`GET /api/events?limit=50`

Returns recent local runtime events.

`WebSocket /ws/events`

Streams live events to the dashboard and integrations. If local auth is enabled, pass `?token=<BINGOMATE_AUTH_TOKEN>` or a bearer token header.

## Context And Proactive Assistance

`GET /api/context?voice_text=hey%20bingo%20summarize%20my%20lab&scene=desk`

Returns a local context snapshot that fuses simulated voice, simulated vision, memory, devices, skills, recent events, identity, and privacy state.

```json
{
  "schema": "bingomate-context/v1",
  "privacy": "local_only",
  "counts": {
    "signals": 8,
    "suggestions": 4
  },
  "signals": [],
  "suggestions": []
}
```

`GET /api/assist/suggestions`

Returns only the proactive suggestions from the current context snapshot. Suggestions are drafts or next-step recommendations; sensitive actions still require explicit approval through the automation/security layer.

## Voice And Vision Simulation

`GET /api/voice/simulate?text=hey%20bingo%20status`

`GET /api/vision/simulate?scene=desk`

Returns a deterministic local vision observation for development without a camera.

`GET /api/vision/status`

Returns camera privacy state, configured camera index, and whether optional local imaging libraries are available.

`POST /api/vision/analyze`

Runs local scene simulation or local uploaded-image heuristics. If `image_base64` is omitted, BingoMate returns a simulated observation for the requested scene. If `image_base64` is provided and Pillow is installed, BingoMate analyzes dimensions, brightness, contrast, dominant color, and heuristic detections without storing the frame.

```json
{
  "scene": "jetson lab desk",
  "image_base64": ""
}
```

`POST /api/vision/capture`

Attempts privacy-gated USB camera capture. Capture requires both `BINGOMATE_CAMERA_ENABLED=1` and request-level `allow_camera: true`. Frames are not stored by default, and `include_frame` defaults to false.

```json
{
  "allow_camera": true,
  "camera_index": 0,
  "width": 640,
  "height": 480,
  "include_frame": false
}
```

`POST /api/voice/turn`

Runs one local voice interaction. If `audio_base64` is present, BingoMate sends it through the configured local STT adapter first; otherwise it uses `audio_hint` as a simulated transcript. If the transcript starts with `hey bingo`, BingoMate strips the wake word, reasons over the request, stores the voice conversation when `remember` is true, emits a `voice.turn` event, and returns the response plus context counts and top suggestions.

```json
{
  "audio_hint": "hey bingo summarize my lab readiness",
  "audio_base64": "",
  "content_type": "audio/wav",
  "remember": true,
  "scene": "desk"
}
```

`GET /api/voice/stt/status`

Reports local STT readiness. OpenAI-compatible local transcription servers and local command wrappers are supported. Simulation fallback remains available when STT is not configured.

`POST /api/voice/transcribe`

Transcribes a local audio payload without storing it. If `audio_base64` is omitted, BingoMate uses `audio_hint` as the simulation fallback.

```json
{
  "audio_base64": "",
  "audio_hint": "hey bingo status",
  "content_type": "audio/wav"
}
```

Audio payloads are bounded to 20 MiB.

`GET /api/voice/say.wav?text=Bingo%20ready`

`POST /api/voice/say.wav`

Returns local WAV audio for the provided text. BingoMate uses `espeak-ng` or `espeak` when available and falls back to an offline prosody WAV so speaker checks still work without model downloads.

```json
{
  "text": "Bingo is ready on the Jetson."
}
```

`GET /api/voice/startup`

Returns the startup phrase used by the display.

`GET /api/voice/startup.wav`

Returns a generated local WAV chime for the boot display.

## Automations

`POST /api/automations/propose`

```json
{
  "trigger": "lab risk alert",
  "action": "update ESP32 matrix",
  "approved": false
}
```

Physical actions are blocked until approved.
