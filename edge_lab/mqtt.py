from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from typing import Any

LOGGER = logging.getLogger("edge-impact")


class NullMqttPublisher:
    enabled = False

    def publish_reading(self, reading: Any) -> None:
        return

    def close(self) -> None:
        return


class PahoMqttPublisher:
    enabled = True

    def __init__(
        self,
        host: str,
        port: int,
        topic: str,
        client_id: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.topic = topic.strip("/")
        self.client_id = client_id
        self.username = username
        self.password = password
        self._client: Any | None = None
        self._connected = False
        self._last_connect_attempt = 0.0

    def publish_reading(self, reading: Any) -> None:
        if not self._ensure_connected():
            return

        payload = build_mqtt_payload(reading)
        body = json.dumps(payload, sort_keys=True)
        self._client.publish(f"{self.topic}/readings", body, qos=0, retain=False)
        self._client.publish(f"{self.topic}/status", payload["status"], qos=0, retain=True)

    def close(self) -> None:
        if self._client is None:
            return
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception as exc:  # pragma: no cover
            LOGGER.debug("MQTT disconnect failed: %s", exc)

    def _ensure_connected(self) -> bool:
        if self._connected:
            return True

        now = time.time()
        if now - self._last_connect_attempt < 10:
            return False
        self._last_connect_attempt = now

        try:
            mqtt = import_paho()
            client = create_client(mqtt, self.client_id)
            if self.username:
                client.username_pw_set(self.username, self.password)
            client.connect(self.host, self.port, keepalive=30)
            client.loop_start()
            self._client = client
            self._connected = True
            LOGGER.info("MQTT publishing enabled for %s:%s topic %s", self.host, self.port, self.topic)
            return True
        except Exception as exc:
            LOGGER.warning("MQTT broker unavailable at %s:%s: %s", self.host, self.port, exc)
            return False


def create_mqtt_publisher(
    host: str | None,
    port: int,
    topic: str,
    client_id: str,
    username: str | None,
    password: str | None,
) -> NullMqttPublisher | PahoMqttPublisher:
    if not host:
        return NullMqttPublisher()
    return PahoMqttPublisher(
        host=host,
        port=port,
        topic=topic,
        client_id=client_id,
        username=username,
        password=password,
    )


def build_mqtt_payload(reading: Any) -> dict[str, Any]:
    payload = asdict(reading)
    payload["schema"] = "edge-impact-reading/v1"
    return payload


def import_paho() -> Any:
    try:
        import paho.mqtt.client as mqtt
    except ImportError as exc:
        raise RuntimeError("install MQTT support with: python -m pip install paho-mqtt") from exc
    return mqtt


def create_client(mqtt: Any, client_id: str) -> Any:
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except (AttributeError, TypeError):
        return mqtt.Client(client_id=client_id)
