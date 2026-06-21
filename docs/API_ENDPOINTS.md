# BingoMate API Reference

## Overview

BingoMate is a FastAPI-based backend providing a comprehensive API for AI companion functionality on Jetson Orin Nano. The API supports voice, vision, memory, automation, and device management.

## Base URL

```
http://127.0.0.1:8090
```

## Authentication

Most endpoints require authentication. Use the `Authorization` header or `X-BingoMate-Token` header.

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://127.0.0.1:8090/api/identity
```

## Core Endpoints

### Health & Status

#### GET /healthz
Health check endpoint, no authentication required.

**Response:**
```json
{
  "ok": true,
  "assistant": "Bingo",
  "simulation": true,
  "reasoning_mode": "local-simulation",
  "auth_required": false,
  "memory_encryption": false
}
```

#### GET /api/auth/status
Check authentication requirements.

**Response:**
```json
{
  "auth_required": false
}
```

#### GET /api/security/status
Check security configuration.

**Response:**
```json
{
  "auth_required": false,
  "memory_encryption": false,
  "device_trust_encryption": false
}
```

### Identity & Context

#### GET /api/identity
Get the current assistant identity and state.

**Response:**
```json
{
  "name": "Bingo",
  "schema": "bingomate-identity/v1",
  "role": "AI Companion",
  "capabilities": [...],
  "devices": [...],
  "skills": [...],
  "memories_count": 42
}
```

#### GET /api/context
Get contextual snapshot with suggestions.

**Query Parameters:**
- `voice_text` (string, default: "hey bingo summarize my lab")
- `scene` (string, default: "desk")

**Response:**
```json
{
  "schema": "bingomate-context/v1",
  "mode": "local-simulation",
  "signals": [...],
  "suggestions": [...]
}
```

#### GET /api/assist/suggestions
Get assistance suggestions based on context.

**Response:**
```json
[
  {
    "id": "suggest-1",
    "title": "Update lab device firmware",
    "priority": "high",
    "requires_approval": true
  }
]
```

### Events

#### GET /api/events
List recent events.

**Query Parameters:**
- `limit` (integer, default: 50)

**Response:**
```json
[
  {
    "id": "event-1",
    "kind": "device.online",
    "timestamp": 1234567890.0,
    "data": {}
  }
]
```

#### WS /ws/events
WebSocket connection for real-time events.

### Reasoning

#### GET /api/reasoning/status
Get reasoning engine status and capabilities.

**Response:**
```json
{
  "schema": "bingomate-reasoning-status/v1",
  "default_mode": "local-simulation",
  "local_llm": {
    "enabled": false,
    "configured": false
  },
  "cloud_assist": {
    "enabled": false
  }
}
```

#### POST /api/reasoning/probe
Send a prompt to the reasoning engine.

**Request Body:**
```json
{
  "prompt": "Summarize BingoMate",
  "include_memories": true
}
```

**Response:**
```json
{
  "schema": "bingomate-reasoning-probe/v1",
  "prompt": "Summarize BingoMate",
  "response": {
    "mode": "local-simulation",
    "response": "..."
  }
}
```

### Memory

#### GET /api/memories
Search or list memories.

**Query Parameters:**
- `q` (string, search query)
- `limit` (integer, default: 20)

**Response:**
```json
[
  {
    "id": 1,
    "kind": "note",
    "content": "Remember to update firmware",
    "importance": 2,
    "tags": ["jetson", "maintenance"],
    "created_at": 1234567890.0
  }
]
```

#### POST /api/memories
Create a new memory.

**Request Body:**
```json
{
  "kind": "note",
  "content": "Bingo startup successful",
  "importance": 1,
  "tags": ["startup", "success"]
}
```

**Response:**
```json
{
  "id": 1,
  "kind": "note",
  "content": "Bingo startup successful",
  "created_at": 1234567890.0
}
```

#### DELETE /api/memories/{id}
Delete a memory.

**Response:**
```json
{
  "success": true,
  "memory_id": 1
}
```

#### GET /api/memories/vector/status
Get vector search status.

**Response:**
```json
{
  "schema": "bingomate-vector-status/v1",
  "enabled": false,
  "model": "not configured"
}
```

#### POST /api/memories/search
Hybrid memory search (text + vector).

**Request Body:**
```json
{
  "query": "jetson setup",
  "mode": "hybrid",
  "limit": 10
}
```

### Voice

#### GET /api/voice/stt/status
Get speech-to-text status.

**Response:**
```json
{
  "schema": "bingomate-stt-status/v1",
  "enabled": false,
  "configured": false,
  "wake_word": "hey bingo",
  "simulation_fallback": true
}
```

#### POST /api/voice/transcribe
Transcribe audio.

**Request Body:**
```json
{
  "audio_base64": "SUQzBAA...",
  "content_type": "audio/wav",
  "audio_hint": "hey bingo status"
}
```

**Response:**
```json
{
  "wake_detected": true,
  "text": "hey bingo status",
  "mode": "local-simulation"
}
```

#### POST /api/voice/turn
Full voice turn (transcribe + respond + synthesize).

**Request Body:**
```json
{
  "audio_base64": "...",
  "content_type": "audio/wav",
  "remember": true,
  "scene": "desk"
}
```

**Response:**
```json
{
  "prompt": "what is your status",
  "response": {...},
  "audio_base64": "...",
  "memory_saved": true
}
```

#### GET /api/voice/say.wav
Synthesize speech (GET version).

**Query Parameters:**
- `text` (string, default: "Bingo ready.")

**Response:** WAV audio file

#### POST /api/voice/say.wav
Synthesize speech (POST version).

**Request Body:**
```json
{
  "text": "Hello from Bingo"
}
```

**Response:** WAV audio file

### Vision

#### GET /api/vision/status
Get vision pipeline status.

**Response:**
```json
{
  "schema": "bingomate-vision-status/v1",
  "camera_enabled": false,
  "privacy": "camera_disabled_until_user_allows",
  "stores_frames_by_default": false
}
```

#### POST /api/vision/analyze
Analyze an image.

**Request Body:**
```json
{
  "image_base64": "iVBORw0KGgo...",
  "scene": "desk"
}
```

**Response:**
```json
{
  "schema": "bingomate-vision-observation/v1",
  "mode": "local-heuristic",
  "scene": "desk",
  "objects": ["person", "workspace"],
  "detections": [...]
}
```

#### POST /api/vision/simulate
Get simulated vision observation.

**Query Parameters:**
- `label` (string, default: "desk")

**Response:** Vision observation

### Skills

#### GET /api/skills
List available skills.

**Response:**
```json
[
  {
    "name": "echo",
    "description": "Echo back the prompt",
    "source": "builtin",
    "requires_approval": false
  }
]
```

#### POST /api/skills/{skill_name}/run
Run a skill.

**Request Body:**
```json
{
  "prompt": "Hello",
  "context": {}
}
```

**Response:**
```json
{
  "ok": true,
  "message": "Skill executed",
  "data": {...}
}
```

#### POST /api/skills
Create a custom skill template.

**Request Body:**
```json
{
  "name": "my_skill",
  "description": "My custom skill",
  "template": "Response to {prompt} in context {context}",
  "requires_approval": true
}
```

#### DELETE /api/skills/{name}
Delete a skill.

**Response:**
```json
{
  "success": true,
  "name": "my_skill"
}
```

### Devices

#### GET /api/devices
List registered devices.

**Response:**
```json
[
  {
    "device_id": "esp32-matrix",
    "name": "LED Matrix",
    "kind": "sensor_node",
    "role": "Display",
    "transport": "mqtt"
  }
]
```

#### POST /api/devices/register
Register a new device.

**Request Body:**
```json
{
  "device_id": "arduino-nano-1",
  "name": "Arduino Sensor",
  "kind": "external_node",
  "shared_secret": "minimum_16_characters_secret"
}
```

**Response:**
```json
{
  "device_id": "arduino-nano-1",
  "registered": true
}
```

#### GET /api/devices/transports
List available device transports.

**Response:**
```json
[
  {
    "name": "mqtt",
    "enabled": false,
    "configured": false
  },
  {
    "name": "ble",
    "enabled": false
  }
]
```

#### POST /api/devices/mqtt/publish
Publish MQTT message from device.

**Request Body:**
```json
{
  "device_id": "esp32-matrix",
  "payload": {"status": "OK"},
  "dry_run": true
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "esp32-matrix",
  "dry_run": true
}
```

### Automation

#### GET /api/automations/status
Get automation engine status.

**Response:**
```json
{
  "schema": "bingomate-automation-status/v1",
  "total_policies": 3,
  "enabled_policies": 2,
  "approved_policies": 1,
  "total_executions": 12
}
```

#### POST /api/automations/propose
Propose an automation action.

**Request Body:**
```json
{
  "trigger": "device_online",
  "action": "send_notification",
  "approved": false
}
```

**Response:**
```json
{
  "trigger": "device_online",
  "action": "send_notification",
  "status": "proposed",
  "requires_user_approval": true
}
```

#### POST /api/automations/policies
Create an automation policy.

**Request Body:**
```json
{
  "trigger": "device_error",
  "action": "alert_user",
  "approved": false
}
```

**Response:**
```json
{
  "policy_id": "policy-abc123",
  "trigger": "device_error",
  "action": "alert_user",
  "enabled": false,
  "approved": false
}
```

#### GET /api/automations/policies
List all automation policies.

**Response:**
```json
[
  {
    "id": "policy-abc123",
    "trigger": "device_online",
    "action": "log_event",
    "enabled": true,
    "approved": true
  }
]
```

#### POST /api/automations/policies/{policy_id}/approve
Approve an automation policy.

**Response:**
```json
{
  "success": true,
  "policy_id": "policy-abc123",
  "approved": true
}
```

#### POST /api/automations/policies/{policy_id}/disable
Disable an automation policy.

**Response:**
```json
{
  "success": true,
  "policy_id": "policy-abc123",
  "disabled": true
}
```

#### DELETE /api/automations/policies/{policy_id}
Delete an automation policy.

**Response:**
```json
{
  "success": true,
  "policy_id": "policy-abc123",
  "deleted": true
}
```

#### GET /api/automations/executions
List recent automation executions.

**Query Parameters:**
- `limit` (integer, default: 50)

**Response:**
```json
[
  {
    "policy_id": "policy-abc123",
    "trigger": "device_online",
    "action": "log_event",
    "executed_at": 1234567890.0,
    "status": "executed"
  }
]
```

### Chat

#### POST /api/chat
Send a chat message.

**Request Body:**
```json
{
  "prompt": "What devices are online?",
  "remember": true
}
```

**Response:**
```json
{
  "mode": "local-simulation",
  "response": "...",
  "requires_cloud": false,
  "memory_saved": true
}
```

## Error Responses

All errors return appropriate HTTP status codes:

- `400`: Bad Request - Invalid parameters
- `401`: Unauthorized - Authentication required
- `404`: Not Found - Resource doesn't exist
- `500`: Internal Server Error

**Error Response Format:**
```json
{
  "detail": "Description of the error"
}
```

## Examples

### Using curl

Health check:
```bash
curl http://127.0.0.1:8090/healthz
```

Create a memory:
```bash
curl -X POST http://127.0.0.1:8090/api/memories \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "note",
    "content": "Remember to check firmware updates",
    "importance": 2,
    "tags": ["maintenance"]
  }'
```

### Using Python

```python
import requests

# Health check
resp = requests.get("http://127.0.0.1:8090/healthz")
print(resp.json())

# Get memories
resp = requests.get("http://127.0.0.1:8090/api/memories?q=jetson")
for memory in resp.json():
    print(f"{memory['content']} (#{memory['id']})")

# Reasoning probe
resp = requests.post("http://127.0.0.1:8090/api/reasoning/probe", json={
    "prompt": "What can you do?",
    "include_memories": True
})
print(resp.json()["response"]["response"])
```

## WebSocket Events

Connect to `/ws/events` to receive real-time events:

```python
import asyncio
import websockets
import json

async def listen():
    uri = "ws://127.0.0.1:8090/ws/events"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            event = json.loads(message)
            print(f"Event: {event['kind']}")

asyncio.run(listen())
```

## Notes

- All timestamps are Unix timestamps (seconds since epoch)
- Base64 encoding is used for binary data (audio, images)
- Simulation mode is enabled by default for development
- Local LLM and STT can be configured via command-line arguments
- All data is stored locally with optional encryption
