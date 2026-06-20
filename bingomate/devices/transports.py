from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from importlib.util import find_spec
from typing import Any


@dataclass(frozen=True)
class TransportStatus:
    name: str
    enabled: bool
    available: bool
    configured: bool
    details: dict[str, object]


class DeviceTransportManager:
    def __init__(
        self,
        mqtt_host: str = "",
        mqtt_port: int = 1883,
        mqtt_topic: str = "bingomate/devices",
        mqtt_username: str = "",
        mqtt_password: str = "",
        ble_enabled: bool = False,
    ) -> None:
        self.mqtt_host = mqtt_host.strip()
        self.mqtt_port = int(mqtt_port)
        self.mqtt_topic = mqtt_topic.strip() or "bingomate/devices"
        self.mqtt_username = mqtt_username.strip()
        self._mqtt_password = mqtt_password
        self.ble_enabled = ble_enabled

    @property
    def mqtt_available(self) -> bool:
        return _module_available("paho.mqtt.client")

    @property
    def mqtt_configured(self) -> bool:
        return bool(self.mqtt_host)

    @property
    def ble_available(self) -> bool:
        return _module_available("bleak")

    def status(self) -> list[TransportStatus]:
        return [
            TransportStatus(
                name="rest",
                enabled=True,
                available=True,
                configured=True,
                details={
                    "endpoint": "/api/devices/{device_id}/messages",
                    "security": "HMAC signed registered-device messages",
                },
            ),
            TransportStatus(
                name="websocket",
                enabled=True,
                available=True,
                configured=True,
                details={
                    "endpoint": "/ws/events",
                    "security": "local auth token when enabled",
                },
            ),
            TransportStatus(
                name="mqtt",
                enabled=self.mqtt_configured,
                available=self.mqtt_available,
                configured=self.mqtt_configured,
                details={
                    "host": self.mqtt_host or "not configured",
                    "port": self.mqtt_port,
                    "topic": self.mqtt_topic,
                    "username_configured": bool(self.mqtt_username),
                    "credential_configured": bool(self.mqtt_username or self._mqtt_password),
                    "dependency": "paho-mqtt" if self.mqtt_available else "install bingomate-edge[mqtt]",
                },
            ),
            TransportStatus(
                name="ble",
                enabled=self.ble_enabled,
                available=self.ble_available,
                configured=self.ble_enabled,
                details={
                    "dependency": "bleak" if self.ble_available else "install bingomate-edge[ble]",
                    "role": "future Nano 33 BLE Sense and wearable sensor bridge",
                },
            ),
        ]

    def status_payload(self) -> dict[str, object]:
        return {
            "schema": "bingomate-device-transports/v1",
            "transports": [asdict(item) for item in self.status()],
        }

    def mqtt_publish(
        self,
        device_id: str,
        payload: dict[str, Any],
        topic: str = "",
        qos: int = 0,
        retain: bool = False,
        dry_run: bool = True,
    ) -> dict[str, object]:
        selected_topic = topic.strip() or self.mqtt_topic
        envelope = self.build_mqtt_envelope(device_id, payload)
        topic_error = _mqtt_topic_error(selected_topic)
        result: dict[str, object] = {
            "schema": "bingomate-mqtt-publish-result/v1",
            "accepted": False,
            "dry_run": dry_run,
            "configured": self.mqtt_configured,
            "available": self.mqtt_available,
            "topic": selected_topic,
            "qos": qos,
            "retain": retain,
            "envelope": envelope,
        }
        if topic_error:
            return {**result, "reason": topic_error}
        if dry_run:
            return {**result, "accepted": True, "reason": "dry_run_not_sent"}
        if not self.mqtt_configured:
            return {**result, "reason": "mqtt_not_configured"}
        if not self.mqtt_available:
            return {**result, "reason": "mqtt_client_missing"}

        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            return {**result, "reason": "mqtt_client_missing"}

        client = mqtt.Client()
        if self.mqtt_username:
            client.username_pw_set(self.mqtt_username, self._mqtt_password or None)
        try:
            client.connect(self.mqtt_host, self.mqtt_port, keepalive=15)
            client.loop_start()
            try:
                message_info = client.publish(
                    selected_topic,
                    json.dumps(envelope, separators=(",", ":"), sort_keys=True),
                    qos=qos,
                    retain=retain,
                )
                message_info.wait_for_publish(timeout=5)
                accepted = bool(getattr(message_info, "is_published", lambda: False)())
                reason = "published" if accepted else f"publish_rc_{getattr(message_info, 'rc', 'unknown')}"
                return {**result, "accepted": accepted, "reason": reason}
            finally:
                client.loop_stop()
        except OSError as exc:
            return {**result, "reason": "mqtt_connect_failed", "error": str(exc)}
        except Exception as exc:
            return {**result, "reason": "mqtt_publish_failed", "error": str(exc)}
        finally:
            try:
                client.disconnect()
            except Exception:
                pass

    def build_mqtt_envelope(self, device_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return {
            "schema": "bingomate-device-mqtt/v1",
            "source": "bingomate",
            "device_id": device_id,
            "timestamp": time.time(),
            "nonce": uuid.uuid4().hex,
            "payload": payload,
        }


def _module_available(module_name: str) -> bool:
    try:
        return find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _mqtt_topic_error(topic: str) -> str:
    if not topic:
        return "mqtt_topic_missing"
    if len(topic) > 256:
        return "mqtt_topic_too_long"
    if "\x00" in topic or "#" in topic or "+" in topic:
        return "mqtt_topic_invalid"
    return ""
