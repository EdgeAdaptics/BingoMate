from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bingomate.security import MemoryCipher

SENSITIVE_METADATA_KEY_PARTS = ("secret", "password", "token", "api_key", "apikey", "credential", "private_key")


@dataclass(frozen=True)
class DeviceRecord:
    id: str
    name: str
    kind: str
    role: str
    transport: str
    status: str
    last_seen: float
    metadata: dict[str, object]


@dataclass(frozen=True)
class DeviceMessageVerification:
    ok: bool
    reason: str


@dataclass(frozen=True)
class DeviceTrustRecord:
    device: DeviceRecord
    hmac_key: bytes | None


class DeviceRegistry:
    def __init__(self, store: "DeviceStore | None" = None) -> None:
        self._devices: dict[str, DeviceRecord] = {}
        self._device_secrets: dict[str, bytes] = {}
        self._seen_nonces: dict[str, set[str]] = {}
        self._store = store
        if self._store:
            for trust_record in self._store.load_devices():
                self._devices[trust_record.device.id] = trust_record.device
                if trust_record.hmac_key:
                    self._device_secrets[trust_record.device.id] = trust_record.hmac_key
                    self._seen_nonces.setdefault(trust_record.device.id, set())

    @property
    def persistent(self) -> bool:
        return self._store is not None

    @property
    def encryption_enabled(self) -> bool:
        return bool(self._store and self._store.encryption_enabled)

    def register(
        self,
        device_id: str,
        name: str,
        kind: str,
        role: str,
        transport: str,
        metadata: dict[str, object] | None = None,
        shared_secret: str = "",
        persist: bool = True,
    ) -> DeviceRecord:
        existing_hmac_key = self._device_secrets.get(device_id)
        safe_metadata = sanitize_device_metadata(metadata or {})
        if shared_secret or existing_hmac_key:
            safe_metadata = {
                **safe_metadata,
                "signed_messages": True,
            }
        record = DeviceRecord(
            id=device_id,
            name=name,
            kind=kind,
            role=role,
            transport=transport,
            status="online",
            last_seen=time.time(),
            metadata=safe_metadata,
        )
        self._devices[device_id] = record
        hmac_key = existing_hmac_key
        if shared_secret:
            hmac_key = derive_device_hmac_key(shared_secret)
            self._device_secrets[device_id] = hmac_key
            self._seen_nonces.setdefault(device_id, set())
        if persist and self._store:
            self._store.save_device(record, hmac_key)
        return record

    def list_devices(self) -> list[DeviceRecord]:
        return sorted(self._devices.values(), key=lambda item: item.id)

    def has_device(self, device_id: str) -> bool:
        return device_id in self._devices

    def verify_signed_message(
        self,
        device_id: str,
        payload: dict[str, Any],
        timestamp: float,
        nonce: str,
        signature: str,
        max_age_seconds: int = 300,
    ) -> DeviceMessageVerification:
        if device_id not in self._devices:
            return DeviceMessageVerification(False, "unknown_device")
        secret = self._device_secrets.get(device_id)
        if not secret:
            return DeviceMessageVerification(False, "device_secret_not_registered")
        if abs(time.time() - timestamp) > max_age_seconds:
            return DeviceMessageVerification(False, "timestamp_out_of_window")
        if not nonce:
            return DeviceMessageVerification(False, "missing_nonce")
        if self._nonce_seen(device_id, nonce):
            return DeviceMessageVerification(False, "replayed_nonce")
        expected = sign_device_message(secret, device_id, payload, timestamp, nonce)
        if not hmac.compare_digest(expected, signature):
            return DeviceMessageVerification(False, "bad_signature")
        self._remember_nonce(device_id, nonce, timestamp)
        return DeviceMessageVerification(True, "verified")

    def seed_simulated_devices(self) -> None:
        if "jetson-orin-nano-super" not in self._devices:
            self.register(
                "jetson-orin-nano-super",
                "Jetson Orin Nano Super",
                "edge_brain",
                "AI brain",
                "local",
                {"simulation": True, "capabilities": ["reasoning", "vision", "voice", "dashboard"]},
                persist=False,
            )
        if "esp32-matrix" not in self._devices:
            self.register(
                "esp32-matrix",
                "ESP32 Matrix Node",
                "automation_node",
                "Status display and IoT actuator",
                "mqtt/serial",
                {"simulation": True, "capabilities": ["matrix_display", "status_alerts"]},
                persist=False,
            )
        if "nano33-ble-sense" not in self._devices:
            self.register(
                "nano33-ble-sense",
                "Arduino Nano 33 BLE Sense",
                "sensor_node",
                "Wearable and environmental sensor",
                "serial/ble",
                {"simulation": True, "capabilities": ["temperature", "humidity", "motion", "sound"]},
                persist=False,
            )

    def _nonce_seen(self, device_id: str, nonce: str) -> bool:
        seen = self._seen_nonces.setdefault(device_id, set())
        return nonce in seen or bool(self._store and self._store.has_nonce(device_id, nonce))

    def _remember_nonce(self, device_id: str, nonce: str, timestamp: float) -> None:
        self._seen_nonces.setdefault(device_id, set()).add(nonce)
        if self._store:
            self._store.remember_nonce(device_id, nonce, timestamp)


class DeviceStore:
    def __init__(self, path: Path | str, cipher: MemoryCipher | None = None) -> None:
        self.path = Path(path)
        self.cipher = cipher
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @property
    def encryption_enabled(self) -> bool:
        return self.cipher is not None

    def init(self) -> None:
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    role TEXT NOT NULL,
                    transport TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_seen REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    hmac_key TEXT NOT NULL,
                    encrypted INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS device_nonces (
                    device_id TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    seen_at REAL NOT NULL,
                    PRIMARY KEY (device_id, nonce)
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def save_device(self, record: DeviceRecord, hmac_key: bytes | None = None) -> None:
        now = time.time()
        stored_key = hmac_key.hex() if hmac_key else ""
        encrypted = 0
        if stored_key and self.cipher:
            stored_key = self.cipher.encrypt_text(stored_key)
            encrypted = 1
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                """
                INSERT INTO devices
                    (id, name, kind, role, transport, status, last_seen, metadata_json, hmac_key, encrypted, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    kind = excluded.kind,
                    role = excluded.role,
                    transport = excluded.transport,
                    status = excluded.status,
                    last_seen = excluded.last_seen,
                    metadata_json = excluded.metadata_json,
                    hmac_key = excluded.hmac_key,
                    encrypted = excluded.encrypted,
                    updated_at = excluded.updated_at
                """,
                (
                    record.id,
                    record.name,
                    record.kind,
                    record.role,
                    record.transport,
                    record.status,
                    record.last_seen,
                    json.dumps(record.metadata, sort_keys=True),
                    stored_key,
                    encrypted,
                    now,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def load_devices(self) -> list[DeviceTrustRecord]:
        conn = sqlite3.connect(self.path)
        try:
            rows = conn.execute(
                """
                SELECT id, name, kind, role, transport, status, last_seen, metadata_json, hmac_key, encrypted
                FROM devices
                ORDER BY id ASC
                """
            ).fetchall()
        finally:
            conn.close()
        return [self._row_to_device(row) for row in rows]

    def has_nonce(self, device_id: str, nonce: str) -> bool:
        conn = sqlite3.connect(self.path)
        try:
            row = conn.execute(
                "SELECT 1 FROM device_nonces WHERE device_id = ? AND nonce = ?",
                (device_id, nonce),
            ).fetchone()
        finally:
            conn.close()
        return row is not None

    def remember_nonce(self, device_id: str, nonce: str, timestamp: float) -> None:
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO device_nonces (device_id, nonce, seen_at) VALUES (?, ?, ?)",
                (device_id, nonce, timestamp),
            )
            conn.execute(
                "DELETE FROM device_nonces WHERE seen_at < ?",
                (time.time() - 86400,),
            )
            conn.commit()
        finally:
            conn.close()

    def _row_to_device(self, row: tuple[Any, ...]) -> DeviceTrustRecord:
        device_id, name, kind, role, transport, status, last_seen, metadata_json, hmac_key, encrypted = row
        stored_key = str(hmac_key)
        if encrypted:
            if not self.cipher:
                stored_key = ""
            else:
                stored_key = self.cipher.decrypt_text(stored_key)
        return DeviceTrustRecord(
            device=DeviceRecord(
                id=str(device_id),
                name=str(name),
                kind=str(kind),
                role=str(role),
                transport=str(transport),
                status=str(status),
                last_seen=float(last_seen),
                metadata=json.loads(metadata_json),
            ),
            hmac_key=bytes.fromhex(stored_key) if stored_key else None,
        )


def derive_device_hmac_key(secret: str | bytes) -> bytes:
    secret_bytes = secret if isinstance(secret, bytes) else secret.encode("utf-8")
    return hashlib.sha256(b"bingomate-device-v1:" + secret_bytes).digest()


def sanitize_device_metadata(metadata: dict[str, object]) -> dict[str, object]:
    return {str(key): _sanitize_metadata_value(str(key), value) for key, value in metadata.items()}


def _sanitize_metadata_value(key: str, value: object) -> object:
    lower_key = key.lower()
    if any(part in lower_key for part in SENSITIVE_METADATA_KEY_PARTS):
        return "[redacted]"
    if isinstance(value, dict):
        return sanitize_device_metadata(value)
    if isinstance(value, list):
        return [_sanitize_metadata_value("", item) for item in value]
    return value


def canonical_device_message(device_id: str, payload: dict[str, Any], timestamp: float, nonce: str) -> bytes:
    body = {
        "device_id": device_id,
        "nonce": nonce,
        "payload": payload,
        "timestamp": timestamp,
    }
    return json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sign_device_message(secret: str | bytes, device_id: str, payload: dict[str, Any], timestamp: float, nonce: str) -> str:
    secret_bytes = secret if isinstance(secret, bytes) else derive_device_hmac_key(secret)
    return hmac.new(
        secret_bytes,
        canonical_device_message(device_id, payload, timestamp, nonce),
        hashlib.sha256,
    ).hexdigest()
