from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
import sys
from io import StringIO
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.util import find_spec
from threading import Thread

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from edge_lab.bridge import LabState, build_reading, fetch_history, init_db, persist_reading, render_prometheus_metrics
from edge_lab.demo import SCENARIOS
from edge_lab.doctor import build_doctor_report, write_doctor_report
from edge_lab.export import read_rows, write_rows
from edge_lab.metrics import parse_sensor_line, score_reading
from edge_lab.mqtt import NullMqttPublisher, build_mqtt_payload
from edge_lab.report import summarize_rows, write_summary
from edge_lab.risk_profile import RiskProfile, load_risk_profile
from scripts.firmware import build_commands, load_manifest
from bingomate.automation import AutomationEngine
from bingomate.context import ContextEngine
from bingomate.core import BingoMateSettings
from bingomate.devices import DeviceRegistry, DeviceStore, DeviceTransportManager, sign_device_message
from bingomate.events import EventBus
from bingomate.identity import IdentityEngine
from bingomate.memory import MemoryStore
from bingomate.reasoning import ReasoningEngine
from bingomate.security import LocalAuth, MemoryCipher, SecurityPolicy
from bingomate.skills import SkillStore, build_default_registry
from bingomate.vision import VisionPipeline
from bingomate.voice import VoicePipeline


class MockLocalLLMHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        payload = json.loads(body.decode("utf-8"))
        assert self.path == "/v1/chat/completions"
        assert payload["model"] == "mock-local-model"
        response = {
            "choices": [
                {
                    "message": {
                        "content": "mock local response",
                    }
                }
            ]
        }
        data = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        return


class MockLocalSTTHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        assert self.path == "/v1/audio/transcriptions"
        assert b'name="model"' in body
        assert b"mock-stt-model" in body
        assert b'name="file"' in body
        response = {"text": "hey bingo mock audio"}
        data = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    payload = parse_sensor_line('{"temperature_c": 42.5, "humidity_pct": 55, "ax": 0.1, "ay": 0.2, "az": 1.5}')
    assert payload is not None
    result = score_reading(payload)
    assert result.status in {"OK", "WARN", "ALERT"}
    assert score_reading(SCENARIOS["impact_event"][1]).status == "ALERT"
    assert score_reading(SCENARIOS["baseline"][0]).status == "OK"
    sensitive_profile = RiskProfile(
        name="test-sensitive",
        temperature_warn_c=35.0,
        sound_alert_level=0.6,
        warn_score=25,
    )
    assert score_reading({"temperature_c": 36.0, "sound_level": 0.65}, sensitive_profile).status == "WARN"
    loaded_profile = load_risk_profile(Path("configs/risk_profile.default.json"))
    assert loaded_profile.name == "default"
    manifest = load_manifest()
    assert "esp32_matrix_status" in manifest["sketches"]
    commands = build_commands("command", manifest["sketches"]["esp32_matrix_status"], "COM4")
    assert commands[0][:3] == ["arduino-cli", "compile", "--fqbn"]
    assert commands[1][0:2] == ["arduino-cli", "upload"]

    reading = build_reading("self-test", payload)
    assert reading.ts <= time.time()
    state = LabState()
    state.update(reading)
    metrics_text = render_prometheus_metrics(state)
    assert "edge_impact_readings_total 1" in metrics_text
    assert f"edge_impact_latest_risk {reading.risk}" in metrics_text
    assert 'edge_impact_status{status="' + reading.status + '"} 1' in metrics_text
    mqtt_payload = build_mqtt_payload(reading)
    assert mqtt_payload["schema"] == "edge-impact-reading/v1"
    assert mqtt_payload["status"] == reading.status
    NullMqttPublisher().publish_reading(reading)

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "edge_lab.db"
        init_db(db_path)
        persist_reading(db_path, reading)
        history = fetch_history(db_path, limit=10)
        assert len(history) == 1
        assert history[0]["source"] == "self-test"
        rows = list(read_rows(db_path))
        assert rows[0]["payload"]["temperature_c"] == 42.5

        csv_output = StringIO()
        write_rows(rows, "csv", csv_output)
        assert "payload_temperature_c" in csv_output.getvalue()

        jsonl_output = StringIO()
        write_rows(rows, "jsonl", jsonl_output)
        assert '"source": "self-test"' in jsonl_output.getvalue()

        summary = summarize_rows(rows)
        assert summary["readings"] == 1
        assert summary["max_risk"] == reading.risk

        markdown_output = StringIO()
        write_summary(summary, "markdown", markdown_output)
        assert "Edge Impact Lab Telemetry Summary" in markdown_output.getvalue()

        doctor_report = build_doctor_report(db_path)
        assert doctor_report["schema"] == "edge-impact-doctor/v1"
        assert any(check["name"] == "publish_preflight" for check in doctor_report["checks"])

        doctor_output = StringIO()
        write_doctor_report(doctor_report, "markdown", doctor_output)
        assert "Edge Impact Lab Doctor" in doctor_output.getvalue()

        memory = MemoryStore(Path(tmp) / "bingomate.db")
        stored_memory = memory.add_memory("preference", "User prefers local-first Jetson workflows", importance=8, tags=["privacy"])
        assert memory.search("Jetson")[0].kind == "preference"
        assert memory.get(int(stored_memory.id or 0)) is not None
        assert len(memory.all_memories()) == 1
        assert memory.add_turn("user", "hello bingo") > 0
        identity_memory = memory.add_memory(
            "preference",
            "Bingo should keep lab replies concise and action-oriented",
            importance=7,
            tags=["identity"],
        )
        assert identity_memory.id is not None
        routine_memory = memory.add_memory(
            "routine",
            "Inspect Arduino vibration sensor before every maintenance demo",
            importance=6,
            tags=["maintenance", "sensor"],
        )
        assert memory.vector_status()["mode"] == "local-hash-vector"
        hybrid_results = memory.vector_search("edge privacy workflow", limit=3)
        assert any(result.memory.kind == "preference" for result in hybrid_results)
        maintenance_results = memory.vector_search("motion maintenance", limit=3)
        assert any(result.memory.id == routine_memory.id for result in maintenance_results)
        assert maintenance_results[0].score > 0
        assert memory.delete_memory(int(stored_memory.id or 0)) is True
        assert memory.get(int(stored_memory.id or 0)) is None
        assert memory.delete_memory(int(stored_memory.id or 0)) is False

        skill_store = SkillStore(Path(tmp) / "bingomate_skills.db")
        skill_definition = skill_store.add_template_skill(
            "lab_brief",
            "Drafts a local lab brief.",
            "Brief for {prompt}. Context: {context}",
            requires_approval=True,
        )
        assert skill_store.get("lab_brief") is not None
        registry = build_default_registry(skill_store)
        assert "echo" in registry.names()
        assert "lab_brief" in registry.names()
        assert registry.run("echo", "test", {"ok": True}).ok
        learned_result = registry.run("lab_brief", "Jetson demo", {"device": "jetson"})
        assert learned_result.ok
        assert "Jetson demo" in str(learned_result.data["output"])
        assert learned_result.data["requires_user_approval"] is True
        assert not registry.run("missing", "test").ok

        device_store = DeviceStore(Path(tmp) / "bingomate_devices.db")
        devices = DeviceRegistry(device_store)
        devices.seed_simulated_devices()
        identity = IdentityEngine("Bingo")
        identity_snapshot = identity.snapshot(
            BingoMateSettings(data_dir=Path(tmp), memory_db=Path(tmp) / "bingomate.db", skills_db=Path(tmp) / "skills.db"),
            devices.list_devices(),
            registry.describe(),
            memory.all_memories(),
            auth_required=True,
            memory_encryption=False,
        )
        assert identity_snapshot["name"] == "Bingo"
        assert identity_snapshot["state"] == "learning"
        assert identity_snapshot["system_awareness"]["device_count"] == 3
        assert identity_snapshot["system_awareness"]["skill_count"] >= 3
        assert identity_snapshot["growth"]["identity_memories"] >= 1
        assert "not a replica" in identity_snapshot["inspiration"]["boundary"]
        assert "Never claim real consciousness" in identity.system_prompt_frame(identity_snapshot)

        context_bus = EventBus()
        context_bus.publish("device.message", {"device_id": "esp32-matrix", "payload": {"status": "ALERT", "risk": 91}})
        context_snapshot = ContextEngine().build_snapshot(
            BingoMateSettings(data_dir=Path(tmp), memory_db=Path(tmp) / "bingomate.db", skills_db=Path(tmp) / "skills.db"),
            identity_snapshot,
            devices.list_devices(),
            registry.describe(),
            memory.all_memories(),
            context_bus.recent(),
            VoicePipeline().simulate_transcript("hey bingo summarize my lab"),
            VisionPipeline().simulate_scene("desk"),
            auth_required=True,
            memory_encryption=False,
        )
        assert context_snapshot["schema"] == "bingomate-context/v1"
        assert context_snapshot["counts"]["signals"] >= 8
        suggestion_ids = {suggestion["id"] for suggestion in context_snapshot["suggestions"]}
        assert "enable-memory-encryption" in suggestion_ids
        assert "bring-up-hardware" in suggestion_ids
        assert "review-device-alerts" in suggestion_ids
        assert "prepare-hands-free-summary" in suggestion_ids

        assert skill_store.delete(skill_definition.name) is True
        assert skill_store.get("lab_brief") is None

        assert any(device.name == "Jetson Orin Nano Super" for device in devices.list_devices())
        devices.register(
            "test-signed-device",
            "Test Signed Device",
            "sensor_node",
            "Signed test node",
            "rest",
            shared_secret="test-shared-secret-123",
        )
        signed_payload = {"temperature_c": 24.2}
        signed_ts = time.time()
        signed_nonce = "nonce-1"
        signature = sign_device_message("test-shared-secret-123", "test-signed-device", signed_payload, signed_ts, signed_nonce)
        assert devices.verify_signed_message("test-signed-device", signed_payload, signed_ts, signed_nonce, signature).ok
        assert not devices.verify_signed_message("test-signed-device", signed_payload, signed_ts, signed_nonce, signature).ok
        assert not devices.verify_signed_message("test-signed-device", signed_payload, signed_ts, "nonce-2", "bad").ok
        updated_device = devices.register(
            "test-signed-device",
            "Test Signed Device",
            "sensor_node",
            "Signed test node",
            "rest",
            metadata={"wifi_password": "should-not-persist", "nested": {"api_token": "should-not-persist", "location": "bench"}},
        )
        assert updated_device.metadata["wifi_password"] == "[redacted]"
        assert updated_device.metadata["nested"]["api_token"] == "[redacted]"
        assert updated_device.metadata["nested"]["location"] == "bench"
        assert updated_device.metadata["signed_messages"] is True
        update_nonce = "nonce-after-metadata-update"
        update_ts = time.time()
        update_signature = sign_device_message("test-shared-secret-123", "test-signed-device", signed_payload, update_ts, update_nonce)
        assert devices.verify_signed_message("test-signed-device", signed_payload, update_ts, update_nonce, update_signature).ok
        reloaded_devices = DeviceRegistry(device_store)
        reloaded_devices.seed_simulated_devices()
        assert reloaded_devices.has_device("test-signed-device")
        signed_nonce_after_restart = "nonce-after-restart"
        signed_ts_after_restart = time.time()
        signature_after_restart = sign_device_message(
            "test-shared-secret-123",
            "test-signed-device",
            signed_payload,
            signed_ts_after_restart,
            signed_nonce_after_restart,
        )
        assert reloaded_devices.verify_signed_message(
            "test-signed-device",
            signed_payload,
            signed_ts_after_restart,
            signed_nonce_after_restart,
            signature_after_restart,
        ).ok
        reloaded_again = DeviceRegistry(device_store)
        assert not reloaded_again.verify_signed_message(
            "test-signed-device",
            signed_payload,
            signed_ts_after_restart,
            signed_nonce_after_restart,
            signature_after_restart,
        ).ok

        transports = DeviceTransportManager()
        transport_state = transports.status_payload()
        transport_names = {item["name"] for item in transport_state["transports"]}
        assert {"rest", "websocket", "mqtt", "ble"}.issubset(transport_names)
        transport_state_text = json.dumps(transport_state).lower()
        assert "password" not in transport_state_text
        dry_run_publish = transports.mqtt_publish("esp32-matrix", {"status": "OK"}, dry_run=True)
        assert dry_run_publish["accepted"] is True
        assert dry_run_publish["dry_run"] is True
        assert dry_run_publish["reason"] == "dry_run_not_sent"
        assert dry_run_publish["envelope"]["schema"] == "bingomate-device-mqtt/v1"
        assert dry_run_publish["envelope"]["device_id"] == "esp32-matrix"
        blocked_publish = transports.mqtt_publish("esp32-matrix", {"status": "OK"}, dry_run=False)
        assert blocked_publish["accepted"] is False
        assert blocked_publish["reason"] == "mqtt_not_configured"
        invalid_topic_publish = transports.mqtt_publish("esp32-matrix", {"status": "OK"}, topic="bingomate/+/devices")
        assert invalid_topic_publish["accepted"] is False
        assert invalid_topic_publish["reason"] == "mqtt_topic_invalid"

        encrypted_device_store_path = Path(tmp) / "encrypted-devices.db"
        encrypted_device_store = DeviceStore(encrypted_device_store_path, cipher=MemoryCipher("device-key-for-self-test"))
        encrypted_devices = DeviceRegistry(encrypted_device_store)
        encrypted_devices.register(
            "encrypted-signed-device",
            "Encrypted Signed Device",
            "sensor_node",
            "Encrypted signed test node",
            "rest",
            shared_secret="encrypted-shared-secret-123",
        )
        conn = sqlite3.connect(encrypted_device_store_path)
        try:
            raw_key, encrypted = conn.execute(
                "SELECT hmac_key, encrypted FROM devices WHERE id = ?",
                ("encrypted-signed-device",),
            ).fetchone()
        finally:
            conn.close()
        assert encrypted == 1
        assert raw_key.startswith(MemoryCipher.prefix)
        assert "encrypted-shared-secret-123" not in raw_key
        encrypted_payload = {"sound_level": 0.42}
        encrypted_ts = time.time()
        encrypted_nonce = "encrypted-nonce-1"
        encrypted_signature = sign_device_message(
            "encrypted-shared-secret-123",
            "encrypted-signed-device",
            encrypted_payload,
            encrypted_ts,
            encrypted_nonce,
        )
        encrypted_reloaded = DeviceRegistry(
            DeviceStore(encrypted_device_store_path, cipher=MemoryCipher("device-key-for-self-test"))
        )
        assert encrypted_reloaded.verify_signed_message(
            "encrypted-signed-device",
            encrypted_payload,
            encrypted_ts,
            encrypted_nonce,
            encrypted_signature,
        ).ok

        response = ReasoningEngine().respond("Prepare my lab demo", ["Remember: local-first"], identity.system_prompt_frame(identity_snapshot))
        assert response["mode"] == "local-simulation"
        assert "Prepare my lab demo" in response["response"]
        reasoning_status = ReasoningEngine().status()
        assert reasoning_status["default_mode"] == "local-simulation"
        assert reasoning_status["local_llm"]["configured"] is False
        mock_server = HTTPServer(("127.0.0.1", 0), MockLocalLLMHandler)
        mock_thread = Thread(target=mock_server.serve_forever, daemon=True)
        mock_thread.start()
        try:
            local_engine = ReasoningEngine(
                local_llm_enabled=True,
                local_llm_url=f"http://127.0.0.1:{mock_server.server_port}",
                local_llm_model="mock-local-model",
                local_llm_timeout_seconds=2,
            )
            local_status = local_engine.status()
            assert local_status["default_mode"] == "local-llm-openai-compatible"
            assert local_status["local_llm"]["configured"] is True
            local_response = local_engine.respond("prepare the local demo", ["memory one"], identity.system_prompt_frame(identity_snapshot))
            assert local_response["mode"] == "local-llm-openai-compatible"
            assert local_response["response"] == "mock local response"
            assert local_response["requires_cloud"] is False
        finally:
            mock_server.shutdown()
            mock_thread.join(timeout=2)

        voice_pipeline = VoicePipeline()
        assert voice_pipeline.simulate_transcript("hey bingo status")["wake_word_detected"] is True
        assert voice_pipeline.simulate_transcript("hey bingo status")["prompt"] == "status"
        assert voice_pipeline.simulate_transcript("status")["wake_word_detected"] is False
        stt_status = voice_pipeline.stt_status()
        assert stt_status["configured"] is False
        assert stt_status["simulation_fallback"] is True
        hint_transcript = voice_pipeline.transcribe_audio_bytes(b"", audio_hint="hey bingo status")
        assert hint_transcript["accepted"] is True
        assert hint_transcript["mode"] == "local-simulation"
        assert hint_transcript["prompt"] == "status"
        mock_stt_server = HTTPServer(("127.0.0.1", 0), MockLocalSTTHandler)
        mock_stt_thread = Thread(target=mock_stt_server.serve_forever, daemon=True)
        mock_stt_thread.start()
        try:
            stt_pipeline = VoicePipeline(
                stt_enabled=True,
                stt_provider="openai-compatible",
                stt_url=f"http://127.0.0.1:{mock_stt_server.server_port}",
                stt_model="mock-stt-model",
                stt_timeout_seconds=2,
            )
            configured_stt_status = stt_pipeline.stt_status()
            assert configured_stt_status["configured"] is True
            audio_transcript = stt_pipeline.transcribe_audio_bytes(b"RIFFmockaudio", content_type="audio/wav")
            assert audio_transcript["accepted"] is True
            assert audio_transcript["mode"] == "local-stt-openai-compatible"
            assert audio_transcript["wake_word_detected"] is True
            assert audio_transcript["prompt"] == "mock audio"
        finally:
            mock_stt_server.shutdown()
            mock_stt_thread.join(timeout=2)
        assert voice_pipeline.prompt_from_transcript("hey bingo prepare the demo") == "prepare the demo"
        assert "Bingo online" in voice_pipeline.startup_phrase("Bingo")
        startup_wav = voice_pipeline.startup_chime_wav()
        assert startup_wav.startswith(b"RIFF")
        assert b"WAVE" in startup_wav[:16]
        assert len(startup_wav) > 1000
        speech = voice_pipeline.synthesize_speech("Bingo is ready for a local voice turn.")
        assert speech.wav.startswith(b"RIFF")
        assert b"WAVE" in speech.wav[:16]
        assert speech.mode in {"local-espeak", "local-prosody-fallback"}
        assert len(speech.wav) > 1000
        display_html = Path("apps/bingo_display/index.html").read_text(encoding="utf-8")
        assert "/display/assets/bingo-boot.gif" in display_html
        assert "local GIF avatar and 3D GUI online" in display_html
        assert " | " in display_html
        assert Path("apps/bingo_display/assets/bingo-boot.gif").stat().st_size > 1000
        dashboard_html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
        assert "/api/voice/turn" in dashboard_html
        assert "/api/voice/say.wav" in dashboard_html
        assert "/api/voice/stt/status" in dashboard_html
        assert "/api/voice/transcribe" in dashboard_html
        assert "/api/reasoning/status" in dashboard_html
        assert "/api/reasoning/probe" in dashboard_html
        assert "/api/memories/search" in dashboard_html
        vision_pipeline = VisionPipeline()
        vision_status = vision_pipeline.status()
        assert vision_status["camera_enabled"] is False
        assert vision_status["stores_frames_by_default"] is False
        simulated_vision = vision_pipeline.simulate_scene("jetson lab desk")
        assert simulated_vision["scene"] == "jetson lab desk"
        assert "jetson" in simulated_vision["objects"]
        assert simulated_vision["detections"]
        disabled_capture = vision_pipeline.capture_camera(allow_camera=True)
        assert disabled_capture["mode"] == "unavailable"
        assert disabled_capture["reason"] == "camera_requires_explicit_enable_and_request"
        invalid_upload = vision_pipeline.analyze_image_base64("not-valid-base64")
        assert invalid_upload["reason"] == "invalid_base64_image"
        if find_spec("PIL") is not None:
            from PIL import Image

            image_path = Path(tmp) / "vision-test.png"
            Image.new("RGB", (24, 16), color=(40, 180, 90)).save(image_path)
            image_observation = vision_pipeline.analyze_image_bytes(image_path.read_bytes())
            assert image_observation["mode"] == "local-image-heuristic"
            assert image_observation["frame"]["width"] == 24
            assert "image_frame" in image_observation["objects"]
        dashboard_html = Path("apps/dashboard/index.html").read_text(encoding="utf-8")
        assert "/api/vision/analyze" in dashboard_html
        assert "/api/vision/capture" in dashboard_html
        assert "/api/devices/transports" in dashboard_html
        assert "/api/devices/mqtt/publish" in dashboard_html

        automation = AutomationEngine().propose("risk alert", "update ESP32 matrix")
        assert automation["status"] == "proposed"
        assert SecurityPolicy().can_execute_action("update ESP32 matrix", approved=False) is False
        assert SecurityPolicy().can_execute_action("update ESP32 matrix", approved=True) is True
        auth = LocalAuth("local-secret")
        assert auth.enabled is True
        assert auth.verify("Bearer local-secret") is True
        assert auth.verify(header_token="local-secret") is True
        assert auth.verify("Bearer wrong") is False
        assert LocalAuth("").verify() is True
        bus = EventBus(max_events=2)
        first_event = bus.publish("test.first", {"ok": True})
        bus.publish("test.second", {})
        bus.publish("test.third", {})
        assert first_event.id == 1
        assert [event.kind for event in bus.recent()] == ["test.second", "test.third"]
        assert bus.recent_as_dicts()[0]["kind"] == "test.second"

        encrypted_db = Path(tmp) / "encrypted-bingomate.db"
        encrypted_memory = MemoryStore(encrypted_db, cipher=MemoryCipher("memory-key-for-self-test"))
        encrypted_record = encrypted_memory.add_memory(
            "preference",
            "Sensitive local preference",
            importance=9,
            tags=["private"],
            metadata={"detail": "sensitive metadata"},
        )
        assert encrypted_memory.encryption_enabled is True
        assert encrypted_memory.get(int(encrypted_record.id or 0)).content == "Sensitive local preference"
        encrypted_vector_results = encrypted_memory.vector_search("private preference", limit=3)
        assert any(result.memory.id == encrypted_record.id for result in encrypted_vector_results)
        conn = sqlite3.connect(encrypted_db)
        try:
            raw_content, raw_metadata, encrypted = conn.execute(
                "SELECT content, metadata_json, encrypted FROM memories WHERE id = ?",
                (encrypted_record.id,),
            ).fetchone()
        finally:
            conn.close()
        assert encrypted == 1
        assert "Sensitive local preference" not in raw_content
        assert "sensitive metadata" not in raw_metadata
        assert raw_content.startswith(MemoryCipher.prefix)

    print("self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
