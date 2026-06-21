from __future__ import annotations

import json
import math
import re
import sqlite3
import time
from dataclasses import asdict, dataclass
from hashlib import blake2b
from pathlib import Path
from typing import Any

from bingomate.security import MemoryCipher

VECTOR_DIMENSIONS = 64
TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "with",
}
SYNONYM_TOKENS = {
    "arduino": ["nano33", "ble", "sensor"],
    "edge": ["jetson", "local", "offline"],
    "iot": ["device", "sensor", "automation"],
    "jetson": ["edge", "nvidia", "orin"],
    "local": ["offline", "privacy", "edge"],
    "maintenance": ["inspection", "routine", "alert"],
    "motion": ["imu", "vibration", "movement"],
    "privacy": ["local", "offline", "private"],
    "reminder": ["schedule", "routine", "task"],
    "sensor": ["telemetry", "arduino", "device"],
}


@dataclass(frozen=True)
class MemoryRecord:
    id: int | None
    kind: str
    content: str
    importance: int
    tags: list[str]
    metadata: dict[str, Any]
    created_at: float


@dataclass(frozen=True)
class MemorySearchResult:
    memory: MemoryRecord
    score: float
    reasons: list[str]


class MemoryStore:
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
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance INTEGER NOT NULL,
                    tags_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    encrypted INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    encrypted INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL
                )
                """
            )
            ensure_column(conn, "memories", "encrypted", "INTEGER NOT NULL DEFAULT 0")
            ensure_column(conn, "conversation_turns", "encrypted", "INTEGER NOT NULL DEFAULT 0")
            conn.commit()
        finally:
            conn.close()

    def add_memory(
        self,
        kind: str,
        content: str,
        importance: int = 1,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        record = MemoryRecord(
            id=None,
            kind=kind,
            content=content,
            importance=max(1, min(10, importance)),
            tags=tags or [],
            metadata=metadata or {},
            created_at=time.time(),
        )
        stored_content = self._encrypt_text(record.content)
        stored_metadata_json = self._encrypt_text(json.dumps(record.metadata, sort_keys=True))
        conn = sqlite3.connect(self.path)
        try:
            cursor = conn.execute(
                """
                INSERT INTO memories (kind, content, importance, tags_json, metadata_json, encrypted, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.kind,
                    stored_content,
                    record.importance,
                    json.dumps(record.tags, sort_keys=True),
                    stored_metadata_json,
                    1 if self.encryption_enabled else 0,
                    record.created_at,
                ),
            )
            conn.commit()
            return MemoryRecord(**{**asdict(record), "id": int(cursor.lastrowid)})
        finally:
            conn.close()

    def add_turn(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> int:
        stored_content = self._encrypt_text(content)
        stored_metadata_json = self._encrypt_text(json.dumps(metadata or {}, sort_keys=True))
        conn = sqlite3.connect(self.path)
        try:
            cursor = conn.execute(
                """
                INSERT INTO conversation_turns (role, content, metadata_json, encrypted, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (role, stored_content, stored_metadata_json, 1 if self.encryption_enabled else 0, time.time()),
            )
            conn.commit()
            return int(cursor.lastrowid)
        finally:
            conn.close()

    def search(self, query: str, limit: int = 20) -> list[MemoryRecord]:
        pattern = f"%{query}%"
        conn = sqlite3.connect(self.path)
        try:
            rows = conn.execute(
                """
                SELECT id, kind, content, importance, tags_json, metadata_json, encrypted, created_at
                FROM memories
                WHERE (encrypted = 0 AND content LIKE ?) OR tags_json LIKE ?
                ORDER BY importance DESC, created_at DESC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            ).fetchall()
        finally:
            conn.close()
        return [row_to_memory(row, self.cipher) for row in rows]

    def vector_status(self) -> dict[str, object]:
        return {
            "schema": "bingomate-memory-vector-status/v1",
            "available": True,
            "mode": "local-hash-vector",
            "dimensions": VECTOR_DIMENSIONS,
            "persistent_index": False,
            "external_model": False,
            "privacy": "vectors are computed in memory from local SQLite rows and are not sent to cloud APIs",
            "encrypted_memory_support": "available when BINGOMATE_MEMORY_KEY is configured",
        }

    def vector_search(self, query: str, limit: int = 20, hybrid: bool = True) -> list[MemorySearchResult]:
        clean_query = query.strip()
        if not clean_query:
            return [
                MemorySearchResult(memory=record, score=0.0, reasons=["recent"])
                for record in self.recent(limit)
            ]
        query_tokens = tokenize_for_memory(clean_query)
        query_vector = hash_vector(query_tokens)
        now = time.time()
        results: list[MemorySearchResult] = []
        for record in self.all_memories():
            if record.content.startswith("[encrypted:"):
                continue
            document_text = memory_document_text(record)
            document_tokens = tokenize_for_memory(document_text)
            vector_score = cosine_similarity(query_vector, hash_vector(document_tokens))
            exact_overlap = len(set(query_tokens) & set(document_tokens))
            if vector_score <= 0 or (exact_overlap == 0 and vector_score < 0.18):
                continue
            importance_boost = record.importance / 100.0
            recency_boost = 1.0 / (1.0 + max(0.0, now - record.created_at) / 86400.0) / 20.0
            exact_boost = exact_overlap / max(10.0, len(set(query_tokens)) * 10.0) if hybrid else 0.0
            score = vector_score + importance_boost + recency_boost + exact_boost
            reasons = ["vector_similarity"]
            if exact_overlap:
                reasons.append("token_overlap")
            if record.importance >= 7:
                reasons.append("high_importance")
            if record.tags:
                reasons.append("tag_context")
            results.append(MemorySearchResult(memory=record, score=round(score, 6), reasons=reasons))
        return sorted(results, key=lambda item: (item.score, item.memory.created_at), reverse=True)[: max(1, min(100, limit))]

    def get(self, memory_id: int) -> MemoryRecord | None:
        conn = sqlite3.connect(self.path)
        try:
            row = conn.execute(
                """
                SELECT id, kind, content, importance, tags_json, metadata_json, encrypted, created_at
                FROM memories
                WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()
        finally:
            conn.close()
        return row_to_memory(row, self.cipher) if row else None

    def recent(self, limit: int = 20) -> list[MemoryRecord]:
        conn = sqlite3.connect(self.path)
        try:
            rows = conn.execute(
                """
                SELECT id, kind, content, importance, tags_json, metadata_json, encrypted, created_at
                FROM memories
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            conn.close()
        return [row_to_memory(row, self.cipher) for row in rows]

    def all_memories(self) -> list[MemoryRecord]:
        conn = sqlite3.connect(self.path)
        try:
            rows = conn.execute(
                """
                SELECT id, kind, content, importance, tags_json, metadata_json, encrypted, created_at
                FROM memories
                ORDER BY created_at ASC
                """
            ).fetchall()
        finally:
            conn.close()
        return [row_to_memory(row, self.cipher) for row in rows]

    def delete_memory(self, memory_id: int) -> bool:
        conn = sqlite3.connect(self.path)
        try:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def _encrypt_text(self, value: str) -> str:
        return self.cipher.encrypt_text(value) if self.cipher else value


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def row_to_memory(row: tuple[Any, ...], cipher: MemoryCipher | None = None) -> MemoryRecord:
    if len(row) == 7:
        memory_id, kind, content, importance, tags_json, metadata_json, created_at = row
        encrypted = 0
    else:
        memory_id, kind, content, importance, tags_json, metadata_json, encrypted, created_at = row
    if encrypted:
        if not cipher:
            content = "[encrypted: BINGOMATE_MEMORY_KEY required]"
            metadata: dict[str, Any] = {"encrypted": True, "key_required": True}
        else:
            content = cipher.decrypt_text(content)
            metadata = json.loads(cipher.decrypt_text(metadata_json))
    else:
        metadata = json.loads(metadata_json)
    return MemoryRecord(
        id=int(memory_id),
        kind=kind,
        content=content,
        importance=int(importance),
        tags=json.loads(tags_json),
        metadata=metadata,
        created_at=float(created_at),
    )


def memory_document_text(record: MemoryRecord) -> str:
    return " ".join(
        [
            record.kind,
            record.content,
            " ".join(record.tags),
            json.dumps(record.metadata, sort_keys=True),
        ]
    )


def tokenize_for_memory(text: str) -> list[str]:
    tokens: list[str] = []
    for raw_token in TOKEN_PATTERN.findall(text.lower()):
        parts = [part for part in raw_token.replace("_", "-").split("-") if part]
        for token in [raw_token, *parts]:
            if len(token) < 2 or token in STOP_WORDS:
                continue
            tokens.append(token)
            tokens.extend(SYNONYM_TOKENS.get(token, []))
    return tokens


def hash_vector(tokens: list[str], dimensions: int = VECTOR_DIMENSIONS) -> list[float]:
    vector = [0.0 for _ in range(dimensions)]
    for token in tokens:
        digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return max(0.0, sum(left_value * right_value for left_value, right_value in zip(left, right)))
