from __future__ import annotations

import base64
import binascii
import csv
import json
from dataclasses import asdict
from io import StringIO
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from bingomate.automation import AutomationEngine
from bingomate.context import ContextEngine
from bingomate.core import BingoMateSettings, default_settings, ensure_data_dir
from bingomate.devices import DeviceRegistry, DeviceStore, DeviceTransportManager
from bingomate.events import EventBus
from bingomate.identity import IdentityEngine
from bingomate.memory import MemoryStore
from bingomate.reasoning import ReasoningEngine
from bingomate.security import LocalAuth, MemoryCipher, SecurityPolicy
from bingomate.skills import SkillStore, TemplateSkill, build_default_registry, validate_skill_name
from bingomate.vision import VisionPipeline
from bingomate.voice import VoicePipeline

MAX_STT_AUDIO_BYTES = 20 * 1024 * 1024


class MemoryCreate(BaseModel):
    kind: str = "note"
    content: str
    importance: int = 1
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    prompt: str
    remember: bool = True


class ReasoningProbeRequest(BaseModel):
    prompt: str = "Summarize BingoMate reasoning runtime in one sentence."
    include_memories: bool = True


class VoiceTurnRequest(BaseModel):
    audio_hint: str = "hey bingo summarize my lab"
    audio_base64: str = ""
    content_type: str = "audio/wav"
    remember: bool = True
    scene: str = "desk"


class VoiceTranscribeRequest(BaseModel):
    audio_base64: str = ""
    audio_hint: str = "hey bingo summarize my lab"
    content_type: str = "audio/wav"


class VoiceSayRequest(BaseModel):
    text: str = Field(min_length=1, max_length=600)


class VisionAnalyzeRequest(BaseModel):
    scene: str = "desk"
    image_base64: str = ""


class VisionCaptureRequest(BaseModel):
    allow_camera: bool = False
    camera_index: int | None = None
    width: int = Field(default=640, ge=160, le=4096)
    height: int = Field(default=480, ge=120, le=2160)
    include_frame: bool = False


class SkillRunRequest(BaseModel):
    prompt: str
    context: dict[str, Any] = Field(default_factory=dict)


class SkillCreateRequest(BaseModel):
    name: str
    description: str
    template: str
    requires_approval: bool = True


class AutomationRequest(BaseModel):
    trigger: str
    action: str
    approved: bool = False


class DeviceRegisterRequest(BaseModel):
    device_id: str
    name: str
    kind: str = "external_node"
    role: str = "Registered device"
    transport: str = "rest"
    shared_secret: str = Field(min_length=16)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceMessageRequest(BaseModel):
    timestamp: float
    nonce: str
    payload: dict[str, Any] = Field(default_factory=dict)
    signature: str


class DeviceMqttPublishRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)
    topic: str = Field(default="", max_length=256)
    qos: int = Field(default=0, ge=0, le=2)
    retain: bool = False
    dry_run: bool = True


def create_app(settings: BingoMateSettings | None = None) -> Any:
    active_settings = settings or default_settings()
    ensure_data_dir(active_settings)

    memory_cipher = MemoryCipher(active_settings.memory_key) if active_settings.memory_key else None
    device_cipher = MemoryCipher(active_settings.device_key) if active_settings.device_key else None
    memory = MemoryStore(active_settings.memory_db, cipher=memory_cipher)
    skill_store = SkillStore(active_settings.skills_db)
    skills = build_default_registry(skill_store)
    device_store = DeviceStore(active_settings.devices_db, cipher=device_cipher)
    devices = DeviceRegistry(device_store)
    devices.seed_simulated_devices()
    transports = DeviceTransportManager(
        mqtt_host=active_settings.mqtt_host,
        mqtt_port=active_settings.mqtt_port,
        mqtt_topic=active_settings.mqtt_topic,
        mqtt_username=active_settings.mqtt_username,
        mqtt_password=active_settings.mqtt_password,
        ble_enabled=active_settings.ble_enabled,
    )
    reasoning = ReasoningEngine(
        cloud_assist=active_settings.cloud_assist,
        openai_model=active_settings.openai_model,
        local_llm_enabled=active_settings.local_llm_enabled,
        local_llm_url=active_settings.local_llm_url,
        local_llm_model=active_settings.local_llm_model,
        local_llm_provider=active_settings.local_llm_provider,
        local_llm_timeout_seconds=active_settings.local_llm_timeout_seconds,
        local_llm_max_tokens=active_settings.local_llm_max_tokens,
    )
    identity = IdentityEngine(active_settings.assistant_name)
    voice = VoicePipeline(
        stt_enabled=active_settings.stt_enabled,
        stt_provider=active_settings.stt_provider,
        stt_url=active_settings.stt_url,
        stt_model=active_settings.stt_model,
        stt_command=active_settings.stt_command,
        stt_timeout_seconds=active_settings.stt_timeout_seconds,
    )
    vision = VisionPipeline(active_settings.camera_enabled, active_settings.camera_index)
    context = ContextEngine()
    automation = AutomationEngine()
    security = SecurityPolicy()
    local_auth = LocalAuth(active_settings.auth_token)
    events = EventBus()

    def require_auth(
        authorization: str | None = Header(default=None),
        x_bingomate_token: str | None = Header(default=None, alias="X-BingoMate-Token"),
    ) -> None:
        if not local_auth.verify(authorization, x_bingomate_token):
            raise HTTPException(
                status_code=401,
                detail="BingoMate local auth token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def normalize_skill_name(name: str) -> str:
        try:
            return validate_skill_name(name)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def relevant_memory_contents(query: str, limit: int = 5) -> list[str]:
        vector_results = memory.vector_search(query, limit=limit, hybrid=True)
        if vector_results:
            return [item.memory.content for item in vector_results]
        return [row.content for row in memory.search(query, limit)]

    def identity_snapshot() -> dict[str, Any]:
        return identity.snapshot(
            settings=active_settings,
            devices=devices.list_devices(),
            skills=skills.describe(),
            memories=memory.all_memories(),
            auth_required=local_auth.enabled,
            memory_encryption=memory.encryption_enabled,
        )

    def context_snapshot(voice_text: str = "hey bingo summarize my lab", scene: str = "desk") -> dict[str, Any]:
        return context.build_snapshot(
            settings=active_settings,
            identity=identity_snapshot(),
            devices=devices.list_devices(),
            skills=skills.describe(),
            memories=memory.all_memories(),
            events=events.recent(limit=50),
            voice_sample=voice.simulate_transcript(voice_text),
            vision_sample=vision.simulate_scene(scene),
            auth_required=local_auth.enabled,
            memory_encryption=memory.encryption_enabled,
        )

    app = FastAPI(
        title="BingoMate",
        version="0.1.0",
        description="Offline-first edge-native personal AI companion for Jetson Orin Nano Super.",
    )

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "ok": True,
            "assistant": active_settings.assistant_name,
            "simulation": active_settings.simulation,
            "cloud_assist": active_settings.cloud_assist,
            "local_llm_enabled": active_settings.local_llm_enabled,
            "reasoning_mode": reasoning.status()["default_mode"],
            "stt_enabled": active_settings.stt_enabled,
            "auth_required": local_auth.enabled,
            "memory_encryption": memory.encryption_enabled,
            "device_trust_encryption": devices.encryption_enabled,
            "camera_enabled": active_settings.camera_enabled,
            "mqtt_configured": transports.mqtt_configured,
            "ble_enabled": active_settings.ble_enabled,
            "memory_db": str(active_settings.memory_db),
            "devices_db": str(active_settings.devices_db),
        }

    @app.get("/api/auth/status")
    def auth_status() -> dict[str, bool]:
        return {"auth_required": local_auth.enabled}

    @app.get("/api/security/status")
    def security_status() -> dict[str, bool]:
        return {
            "auth_required": local_auth.enabled,
            "memory_encryption": memory.encryption_enabled,
            "device_trust_encryption": devices.encryption_enabled,
        }

    @app.get("/api/identity")
    def get_identity(_auth: None = Depends(require_auth)) -> dict[str, Any]:
        return identity_snapshot()

    @app.get("/api/events")
    def list_events(limit: int = 50, _auth: None = Depends(require_auth)) -> list[dict[str, Any]]:
        return events.recent_as_dicts(limit)

    @app.get("/api/context")
    def get_context(
        voice_text: str = "hey bingo summarize my lab",
        scene: str = "desk",
        _auth: None = Depends(require_auth),
    ) -> dict[str, Any]:
        return context_snapshot(voice_text, scene)

    @app.get("/api/assist/suggestions")
    def get_assistance_suggestions(
        voice_text: str = "hey bingo summarize my lab",
        scene: str = "desk",
        _auth: None = Depends(require_auth),
    ) -> list[dict[str, Any]]:
        return context_snapshot(voice_text, scene)["suggestions"]

    @app.get("/api/reasoning/status")
    def reasoning_status(_auth: None = Depends(require_auth)) -> dict[str, object]:
        return reasoning.status()

    @app.post("/api/reasoning/probe")
    def reasoning_probe(request: ReasoningProbeRequest, _auth: None = Depends(require_auth)) -> dict[str, object]:
        relevant = relevant_memory_contents(request.prompt, limit=5) if request.include_memories else []
        response = reasoning.respond(request.prompt, relevant, identity.system_prompt_frame(identity_snapshot()))
        events.publish(
            "reasoning.probe",
            {
                "mode": response["mode"],
                "local_llm_enabled": active_settings.local_llm_enabled,
                "include_memories": request.include_memories,
            },
        )
        return {
            "schema": "bingomate-reasoning-probe/v1",
            "prompt": request.prompt,
            "memory_count": len(relevant),
            "response": response,
        }

    @app.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket, token: str = "") -> None:
        if not local_auth.verify(websocket.headers.get("authorization"), token):
            await websocket.close(code=1008)
            return

        await websocket.accept()
        for event in events.recent(limit=20):
            await websocket.send_json(asdict(event))

        subscriber = events.subscribe()
        try:
            while True:
                event = await subscriber.queue.get()
                await websocket.send_json(asdict(event))
        except WebSocketDisconnect:
            pass
        finally:
            events.unsubscribe(subscriber)

    @app.get("/")
    def dashboard() -> Any:
        index_path = active_settings.dashboard_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "BingoMate API is running", "dashboard": str(index_path)}

    @app.get("/display")
    def bingo_display() -> Any:
        index_path = active_settings.display_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "Bingo display app is missing", "display": str(index_path)}

    @app.get("/display/assets/{asset_path:path}")
    def bingo_display_asset(asset_path: str) -> Any:
        asset_root = (active_settings.display_dir / "assets").resolve()
        target = (asset_root / asset_path).resolve()
        try:
            target.relative_to(asset_root)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Display asset not found.") from exc
        if not target.is_file():
            raise HTTPException(status_code=404, detail="Display asset not found.")
        return FileResponse(target)

    @app.get("/api/voice/startup")
    def startup_voice() -> dict[str, str]:
        return {"text": voice.startup_phrase(active_settings.assistant_name)}

    @app.get("/api/voice/startup.wav")
    def startup_chime() -> Response:
        return Response(voice.startup_chime_wav(), media_type="audio/wav")

    @app.get("/api/voice/stt/status")
    def voice_stt_status(_auth: None = Depends(require_auth)) -> dict[str, object]:
        return voice.stt_status()

    @app.post("/api/voice/transcribe")
    def voice_transcribe(request: VoiceTranscribeRequest, _auth: None = Depends(require_auth)) -> dict[str, object]:
        audio = decode_audio_base64(request.audio_base64)
        transcript = voice.transcribe_audio_bytes(audio, request.content_type, request.audio_hint)
        events.publish(
            "voice.transcribed",
            {
                "mode": transcript.get("mode"),
                "accepted": transcript.get("accepted"),
                "reason": transcript.get("reason"),
                "wake_word_detected": transcript.get("wake_word_detected"),
                "audio_bytes": len(audio),
            },
        )
        return transcript

    @app.get("/api/voice/say.wav")
    def voice_say_get(text: str = "Bingo ready.", _auth: None = Depends(require_auth)) -> Response:
        synthesis = voice.synthesize_speech(text)
        return Response(
            synthesis.wav,
            media_type="audio/wav",
            headers={"X-BingoMate-Voice-Mode": synthesis.mode},
        )

    @app.post("/api/voice/say.wav")
    def voice_say_post(request: VoiceSayRequest, _auth: None = Depends(require_auth)) -> Response:
        synthesis = voice.synthesize_speech(request.text)
        return Response(
            synthesis.wav,
            media_type="audio/wav",
            headers={"X-BingoMate-Voice-Mode": synthesis.mode},
        )

    @app.get("/api/memories")
    def list_memories(_auth: None = Depends(require_auth), q: str = "", limit: int = 20) -> list[dict[str, Any]]:
        rows = memory.search(q, limit) if q else memory.recent(limit)
        return [asdict(row) for row in rows]

    @app.get("/api/memories/vector/status")
    def memory_vector_status(_auth: None = Depends(require_auth)) -> dict[str, object]:
        return memory.vector_status()

    @app.get("/api/memories/search")
    def search_memories(
        q: str = "",
        mode: str = "hybrid",
        limit: int = 20,
        _auth: None = Depends(require_auth),
    ) -> dict[str, object]:
        selected_mode = mode if mode in {"text", "vector", "hybrid"} else "hybrid"
        bounded_limit = max(1, min(100, limit))
        if not q.strip():
            return {
                "schema": "bingomate-memory-search/v1",
                "query": q,
                "mode": "recent",
                "vector_status": memory.vector_status(),
                "results": [
                    {"score": 0.0, "reasons": ["recent"], "memory": asdict(row)}
                    for row in memory.recent(bounded_limit)
                ],
            }
        if selected_mode == "text":
            results = [
                {"score": 1.0, "reasons": ["text_match"], "memory": asdict(row)}
                for row in memory.search(q, bounded_limit)
            ]
        else:
            results = [
                {"score": item.score, "reasons": item.reasons, "memory": asdict(item.memory)}
                for item in memory.vector_search(q, bounded_limit, hybrid=selected_mode == "hybrid")
            ]
        return {
            "schema": "bingomate-memory-search/v1",
            "query": q,
            "mode": selected_mode,
            "vector_status": memory.vector_status(),
            "results": results,
        }

    @app.post("/api/memories")
    def add_memory(request: MemoryCreate, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        record = memory.add_memory(
            kind=request.kind,
            content=request.content,
            importance=request.importance,
            tags=request.tags,
            metadata=request.metadata,
        )
        events.publish("memory.created", {"id": record.id, "kind": record.kind, "tags": record.tags})
        return asdict(record)

    @app.delete("/api/memories/{memory_id}")
    def delete_memory(memory_id: int, _auth: None = Depends(require_auth)) -> dict[str, object]:
        if not memory.delete_memory(memory_id):
            raise HTTPException(status_code=404, detail="Memory not found.")
        events.publish("memory.deleted", {"id": memory_id})
        return {"deleted": True, "id": memory_id}

    @app.get("/api/memories/export")
    def export_memories(format: str = "jsonl", _auth: None = Depends(require_auth)) -> Any:
        rows = [asdict(row) for row in memory.all_memories()]
        if format == "json":
            return {"schema": "bingomate-memory-export/v1", "memories": rows}
        if format == "csv":
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=["id", "kind", "content", "importance", "tags", "metadata", "created_at"])
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "id": row["id"],
                        "kind": row["kind"],
                        "content": row["content"],
                        "importance": row["importance"],
                        "tags": json.dumps(row["tags"], sort_keys=True),
                        "metadata": json.dumps(row["metadata"], sort_keys=True),
                        "created_at": row["created_at"],
                    }
                )
            return Response(output.getvalue(), media_type="text/csv")
        if format != "jsonl":
            raise HTTPException(status_code=400, detail="Supported formats: jsonl, json, csv.")
        payload = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
        return Response((payload + "\n") if payload else "", media_type="application/x-ndjson")

    @app.post("/api/chat")
    def chat(request: ChatRequest, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        relevant = relevant_memory_contents(request.prompt, limit=5)
        response = reasoning.respond(request.prompt, relevant, identity.system_prompt_frame(identity_snapshot()))
        memory.add_turn("user", request.prompt)
        memory.add_turn("assistant", str(response["response"]), {"mode": response["mode"]})
        if request.remember:
            memory.add_memory("conversation", request.prompt, importance=2, tags=["conversation"])
        events.publish("chat.completed", {"mode": response["mode"], "remembered": request.remember})
        return response

    @app.post("/api/voice/turn")
    def voice_turn(request: VoiceTurnRequest, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        if request.audio_base64:
            transcript = voice.transcribe_audio_bytes(
                decode_audio_base64(request.audio_base64),
                request.content_type,
                request.audio_hint,
            )
        else:
            transcript = voice.simulate_transcript(request.audio_hint)
        prompt = str(transcript.get("prompt", ""))
        if not transcript.get("wake_word_detected"):
            response = {
                "mode": "local-voice-standby",
                "response": f"Wake word not detected. Start with '{voice.wake_word}' or use text chat.",
                "requires_cloud": False,
            }
            events.publish("voice.ignored", {"wake_word_detected": False, "text": transcript.get("text", "")})
            return {
                "schema": "bingomate-voice-turn/v1",
                "accepted": False,
                "transcript": transcript,
                "prompt": "",
                "response": response,
                "audio_endpoint": "/api/voice/say.wav",
            }

        relevant = relevant_memory_contents(prompt, limit=5)
        response = reasoning.respond(prompt, relevant, identity.system_prompt_frame(identity_snapshot()))
        if request.remember:
            memory.add_turn("user", str(transcript.get("text", "")), {"mode": "voice", "wake_word_detected": True})
            memory.add_turn("assistant", str(response["response"]), {"mode": response["mode"], "source": "voice"})
            memory.add_memory("conversation", prompt, importance=2, tags=["conversation", "voice"])
        event = events.publish(
            "voice.turn",
            {
                "wake_word_detected": True,
                "prompt": prompt,
                "mode": response["mode"],
                "remembered": request.remember,
            },
        )
        context_summary = context_snapshot(str(transcript.get("text", "")), request.scene)
        return {
            "schema": "bingomate-voice-turn/v1",
            "accepted": True,
            "transcript": transcript,
            "prompt": prompt,
            "response": response,
            "audio_endpoint": "/api/voice/say.wav",
            "context_counts": context_summary["counts"],
            "suggestions": context_summary["suggestions"][:3],
            "event": asdict(event),
        }

    @app.get("/api/skills")
    def list_skills(_auth: None = Depends(require_auth)) -> list[dict[str, object]]:
        return skills.describe()

    @app.post("/api/skills")
    def create_skill(request: SkillCreateRequest, _auth: None = Depends(require_auth)) -> dict[str, object]:
        normalized_name = normalize_skill_name(request.name)
        if normalized_name in skills.names():
            raise HTTPException(status_code=409, detail=f"Skill already exists: {normalized_name}")
        try:
            definition = skill_store.add_template_skill(
                name=normalized_name,
                description=request.description,
                template=request.template,
                requires_approval=request.requires_approval,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        skills.register(TemplateSkill(definition))
        events.publish("skill.created", {"name": definition.name, "requires_approval": definition.requires_approval})
        return {
            "name": definition.name,
            "description": definition.description,
            "source": "local-template",
            "requires_approval": definition.requires_approval,
        }

    @app.delete("/api/skills/{skill_name}")
    def delete_skill(skill_name: str, _auth: None = Depends(require_auth)) -> dict[str, object]:
        normalized_name = normalize_skill_name(skill_name)
        existing = skill_store.get(normalized_name)
        if not existing:
            raise HTTPException(status_code=404, detail="Only local template skills can be deleted.")
        if not skill_store.delete(normalized_name):
            raise HTTPException(status_code=404, detail="Skill not found.")
        skills.unregister(normalized_name)
        events.publish("skill.deleted", {"name": normalized_name})
        return {"deleted": True, "name": normalized_name}

    @app.post("/api/skills/{skill_name}/run")
    def run_skill(skill_name: str, request: SkillRunRequest, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        normalized_name = normalize_skill_name(skill_name)
        result = skills.run(normalized_name, request.prompt, request.context)
        if not result.ok:
            raise HTTPException(status_code=404, detail=result.message)
        events.publish("skill.ran", {"name": normalized_name, "ok": result.ok})
        return asdict(result)

    @app.get("/api/devices")
    def list_devices(_auth: None = Depends(require_auth)) -> list[dict[str, Any]]:
        return [asdict(device) for device in devices.list_devices()]

    @app.post("/api/devices/register")
    def register_device(request: DeviceRegisterRequest, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        record = devices.register(
            device_id=request.device_id,
            name=request.name,
            kind=request.kind,
            role=request.role,
            transport=request.transport,
            metadata=request.metadata,
            shared_secret=request.shared_secret,
        )
        events.publish("device.registered", {"id": record.id, "name": record.name, "transport": record.transport})
        return asdict(record)

    @app.post("/api/devices/{device_id}/messages")
    def receive_device_message(device_id: str, request: DeviceMessageRequest, _auth: None = Depends(require_auth)) -> dict[str, object]:
        verification = devices.verify_signed_message(
            device_id=device_id,
            payload=request.payload,
            timestamp=request.timestamp,
            nonce=request.nonce,
            signature=request.signature,
        )
        if not verification.ok:
            raise HTTPException(status_code=401, detail=verification.reason)
        event = events.publish("device.message", {"device_id": device_id, "payload": request.payload})
        return {"accepted": True, "event": asdict(event)}

    @app.get("/api/devices/transports")
    def list_device_transports(_auth: None = Depends(require_auth)) -> dict[str, object]:
        return transports.status_payload()

    @app.post("/api/devices/mqtt/publish")
    def publish_device_mqtt(request: DeviceMqttPublishRequest, _auth: None = Depends(require_auth)) -> dict[str, object]:
        if not devices.has_device(request.device_id):
            raise HTTPException(status_code=404, detail="Device is not registered.")
        result = transports.mqtt_publish(
            device_id=request.device_id,
            payload=request.payload,
            topic=request.topic,
            qos=request.qos,
            retain=request.retain,
            dry_run=request.dry_run,
        )
        events.publish(
            "device.mqtt.publish",
            {
                "device_id": request.device_id,
                "accepted": result["accepted"],
                "dry_run": result["dry_run"],
                "reason": result["reason"],
                "topic": result["topic"],
            },
        )
        return result

    @app.get("/api/vision/simulate")
    def simulate_vision(scene: str = "desk", _auth: None = Depends(require_auth)) -> dict[str, object]:
        return vision.simulate_scene(scene)

    @app.get("/api/vision/status")
    def vision_status(_auth: None = Depends(require_auth)) -> dict[str, object]:
        return vision.status()

    @app.post("/api/vision/analyze")
    def analyze_vision(request: VisionAnalyzeRequest, _auth: None = Depends(require_auth)) -> dict[str, object]:
        if request.image_base64:
            observation = vision.analyze_image_base64(request.image_base64, "upload")
        else:
            observation = vision.simulate_scene(request.scene)
        events.publish(
            "vision.analyzed",
            {
                "mode": observation.get("mode"),
                "scene": observation.get("scene"),
                "object_count": len(observation.get("objects", [])),
            },
        )
        return observation

    @app.post("/api/vision/capture")
    def capture_vision(request: VisionCaptureRequest, _auth: None = Depends(require_auth)) -> dict[str, object]:
        observation = vision.capture_camera(
            allow_camera=request.allow_camera,
            camera_index=request.camera_index,
            width=request.width,
            height=request.height,
            include_frame=request.include_frame,
        )
        events.publish(
            "vision.capture",
            {
                "mode": observation.get("mode"),
                "reason": observation.get("reason", ""),
                "include_frame": request.include_frame,
                "camera": observation.get("camera", {}),
            },
        )
        return observation

    @app.get("/api/voice/simulate")
    def simulate_voice(text: str = "hey bingo summarize my lab", _auth: None = Depends(require_auth)) -> dict[str, object]:
        return voice.simulate_transcript(text)

    @app.post("/api/automations/propose")
    def propose_automation(request: AutomationRequest, _auth: None = Depends(require_auth)) -> dict[str, object]:
        if not security.can_execute_action(request.action, request.approved):
            events.publish("automation.blocked", {"trigger": request.trigger, "action": request.action})
            return {
                "status": "blocked",
                "reason": "User approval required before executing this action.",
                "proposal": automation.propose(request.trigger, request.action),
            }
        proposal = automation.propose(request.trigger, request.action)
        events.publish("automation.proposed", {"trigger": request.trigger, "action": request.action})
        return proposal

    return app


def decode_audio_base64(audio_base64: str) -> bytes:
    if not audio_base64:
        return b""
    try:
        audio = base64.b64decode(audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 audio payload.") from exc
    if len(audio) > MAX_STT_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio payload exceeds 20 MiB.")
    return audio
