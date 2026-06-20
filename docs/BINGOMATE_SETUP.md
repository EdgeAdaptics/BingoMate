# BingoMate Setup

## PC Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
bingomate-api --host 127.0.0.1 --port 8090
```

Open `http://127.0.0.1:8090`.

Open the character display at `http://127.0.0.1:8090/display`.

## Jetson Development

After logging into the Jetson and configuring Wi-Fi:

```bash
git clone https://github.com/EdgeAdaptics/BingoMate.git
cd BingoMate
bash scripts/jetson_prepare.sh
source .venv/bin/activate
bingomate-api --host 0.0.0.0 --port 8090
```

Use `--host 0.0.0.0` only on a trusted lab network. Set `BINGOMATE_AUTH_TOKEN` before exposing the dashboard beyond localhost.

## Local Authentication

BingoMate binds to localhost by default. When exposing the dashboard on a lab network, set a local token:

```powershell
$env:BINGOMATE_AUTH_TOKEN="<do-not-commit>"
bingomate-api --host 0.0.0.0 --port 8090
```

The dashboard stores the token only in browser local storage. API clients can send `Authorization: Bearer <token>` or `X-BingoMate-Token: <token>`.

## Encrypted Local Memory

Set a high-entropy memory key before first use to encrypt memory content, conversation turns, and memory metadata at rest:

```powershell
$env:BINGOMATE_MEMORY_KEY="<high-entropy-local-key>"
bingomate-api --host 127.0.0.1 --port 8090
```

Keep this key out of git; store it in a password manager or OS secret store. If the key is lost, encrypted rows cannot be decrypted. Tags remain plaintext so local search and filtering can still work without decrypting every row.

Memory search has no extra dependency. Text search uses SQLite, and hybrid/vector modes compute local hash vectors in memory:

```powershell
curl http://127.0.0.1:8090/api/memories/vector/status
curl "http://127.0.0.1:8090/api/memories/search?q=privacy%20workflow&mode=hybrid"
```

No memory vectors are sent to cloud APIs. No vector values are persisted by default.

## Encrypted Device Trust

Registered ESP32, Arduino, Raspberry Pi, and other lab devices persist in `BINGOMATE_DEVICES_DB`. BingoMate stores a derived HMAC key, not the raw shared secret. Set `BINGOMATE_DEVICE_KEY` to encrypt derived device HMAC keys at rest:

```powershell
$env:BINGOMATE_DEVICE_KEY="<high-entropy-local-device-key>"
bingomate-api --host 127.0.0.1 --port 8090
```

If `BINGOMATE_DEVICE_KEY` is unset, it falls back to `BINGOMATE_MEMORY_KEY` when that key exists. Replay nonces are persisted so signed device messages cannot be replayed after service restart.

## Optional Device Transports

REST and WebSocket are available with the base install. MQTT and BLE are optional so the same code runs on a laptop, WSL, or Jetson before all hardware is attached:

```powershell
python -m pip install -e ".[mqtt,ble]"
$env:BINGOMATE_MQTT_HOST="127.0.0.1"
$env:BINGOMATE_MQTT_PORT="1883"
$env:BINGOMATE_MQTT_TOPIC="bingomate/devices"
$env:BINGOMATE_BLE_ENABLED="1"
bingomate-api --host 127.0.0.1 --port 8090
```

Check readiness and run a broker-free MQTT envelope dry-run:

```powershell
curl http://127.0.0.1:8090/api/devices/transports
curl -X POST http://127.0.0.1:8090/api/devices/mqtt/publish -H "Content-Type: application/json" -d "{\"device_id\":\"esp32-matrix\",\"payload\":{\"status\":\"OK\"},\"dry_run\":true}"
```

Put MQTT usernames and passwords in environment variables or a local `.env` file that is not committed. The transport status reports whether credentials are configured without exposing their values.

## Optional Codex CLI On Jetson

```bash
INSTALL_CODEX_CLI=1 bash scripts/jetson_prepare.sh
codex login
codex doctor
```

See `docs/CODEX_ON_JETSON.md`.

## Optional Boot Display On Jetson

To boot directly into Bingo's full-screen animated character display on an attached monitor:

```bash
bash scripts/install_bingomate_display_service.sh
```

See `docs/BOOT_DISPLAY.md` for Chromium kiosk, startup chime, voice, and token handling.

## Optional Local Voice Output

The voice-turn API works without model downloads:

```powershell
curl -X POST http://127.0.0.1:8090/api/voice/turn -H "Content-Type: application/json" -d "{\"audio_hint\":\"hey bingo summarize my lab readiness\"}"
```

Install `espeak-ng` on Jetson for lightweight local speech WAV output. If it is missing, BingoMate still returns an offline prosody WAV for speaker checks:

```bash
sudo apt-get install -y espeak-ng
```

To use a local speech-to-text server that exposes OpenAI-compatible audio transcription:

```powershell
$env:BINGOMATE_STT_ENABLED="1"
$env:BINGOMATE_STT_PROVIDER="openai-compatible"
$env:BINGOMATE_STT_URL="http://127.0.0.1:8081"
$env:BINGOMATE_STT_MODEL="<local-stt-model-name>"
bingomate-api --host 127.0.0.1 --port 8090
```

For a local command wrapper such as whisper.cpp, provide a command template. BingoMate replaces `{audio}` with a temporary local audio path and `{model}` with `BINGOMATE_STT_MODEL`:

```powershell
$env:BINGOMATE_STT_ENABLED="1"
$env:BINGOMATE_STT_PROVIDER="command"
$env:BINGOMATE_STT_MODEL="models/ggml-base.en.bin"
$env:BINGOMATE_STT_COMMAND="whisper-cli -m {model} -f {audio} --no-timestamps"
```

Check status or run a non-storing transcription fallback:

```powershell
curl http://127.0.0.1:8090/api/voice/stt/status
curl -X POST http://127.0.0.1:8090/api/voice/transcribe -H "Content-Type: application/json" -d "{\"audio_hint\":\"hey bingo status\"}"
```

## Optional Local Camera Vision

Vision APIs run in simulation by default. USB camera capture is deliberately disabled until both the environment and request allow it:

```powershell
$env:BINGOMATE_CAMERA_ENABLED="1"
$env:BINGOMATE_CAMERA_INDEX="0"
bingomate-api --host 127.0.0.1 --port 8090
```

Then call:

```powershell
curl -X POST http://127.0.0.1:8090/api/vision/capture -H "Content-Type: application/json" -d "{\"allow_camera\":true,\"include_frame\":false}"
```

Install OpenCV only when physical capture is needed. Uploaded-image heuristic analysis and simulation remain useful without a camera.

## Optional Local LLM Runtime

BingoMate is designed to use a local Jetson model server before any cloud path. Start a local OpenAI-compatible server such as llama.cpp, vLLM, or a compatible TensorRT-LLM gateway, then configure:

```powershell
$env:BINGOMATE_LOCAL_LLM_ENABLED="1"
$env:BINGOMATE_LOCAL_LLM_PROVIDER="openai-compatible"
$env:BINGOMATE_LOCAL_LLM_URL="http://127.0.0.1:8080"
$env:BINGOMATE_LOCAL_LLM_MODEL="<local-model-name>"
bingomate-api --host 127.0.0.1 --port 8090
```

For Ollama-style local chat APIs:

```powershell
$env:BINGOMATE_LOCAL_LLM_ENABLED="1"
$env:BINGOMATE_LOCAL_LLM_PROVIDER="ollama"
$env:BINGOMATE_LOCAL_LLM_URL="http://127.0.0.1:11434"
$env:BINGOMATE_LOCAL_LLM_MODEL="<ollama-model-name>"
```

Check status and run a non-persistent probe:

```powershell
curl http://127.0.0.1:8090/api/reasoning/status
curl -X POST http://127.0.0.1:8090/api/reasoning/probe -H "Content-Type: application/json" -d "{\"prompt\":\"Confirm local reasoning is online\",\"include_memories\":false}"
```

If the local endpoint is unavailable, BingoMate falls back to deterministic local simulation. It does not silently use cloud APIs unless cloud assist is explicitly enabled.

## Optional OpenAI Cloud Assist

BingoMate is local-first. Cloud assistance should be opt-in:

```powershell
python -m pip install -e ".[cloud]"
$env:BINGOMATE_CLOUD_ASSIST="1"
$env:BINGOMATE_OPENAI_MODEL="<available-responses-api-model>"
$env:OPENAI_API_KEY="<do-not-commit>"
```

Do not put real API keys in tracked files. The runtime stays deterministic unless cloud assist is explicitly enabled. When enabled, the guarded adapter uses the OpenAI Responses API through the official Python SDK and sends only the current prompt plus the top local memories selected by BingoMate.

## Docker

```powershell
docker compose -f deploy\docker-compose.yml up --build
```

Open `http://127.0.0.1:8090`.

## Validation

```powershell
python -m compileall bingomate edge_lab scripts
python scripts\self_test.py
python scripts\preflight_publish.py
```
