"""Tests for the memory store module."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from bingomate.memory import MemoryRecord, MemoryStore


@pytest.fixture
def temp_memory_db() -> Path:
    """Create a temporary database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        yield db_path


def test_memory_store_init(temp_memory_db: Path) -> None:
    """Test memory store initialization."""
    store = MemoryStore(temp_memory_db)
    assert store.path == temp_memory_db
    assert store.encryption_enabled is False


def test_memory_store_create_and_retrieve(temp_memory_db: Path) -> None:
    """Test creating and retrieving a memory."""
    store = MemoryStore(temp_memory_db)
    
    # Create a memory
    memory = store.add_memory("test", "Hello world", 1)
    assert memory.id is not None
    assert memory.id > 0
    assert memory.content == "Hello world"
    assert memory.kind == "test"
    
    # Retrieve it
    retrieved = store.get(memory.id)
    assert retrieved is not None
    assert retrieved.content == "Hello world"
    assert retrieved.kind == "test"


def test_memory_store_search(temp_memory_db: Path) -> None:
    """Test searching memories."""
    store = MemoryStore(temp_memory_db)
    
    # Create multiple memories
    store.add_memory("note", "Jetson configuration tips", 1)
    store.add_memory("note", "Privacy-first architecture", 1)
    store.add_memory("reminder", "Update firmware", 2)
    
    # Search
    results = store.search("Jetson", limit=10)
    assert len(results) >= 1
    assert any("Jetson" in r.content for r in results)


def test_memory_store_tags(temp_memory_db: Path) -> None:
    """Test memory tags."""
    store = MemoryStore(temp_memory_db)
    
    # Create memory with tags
    memory = store.add_memory(
        "note",
        "Development setup",
        1,
        tags=["jetson", "setup", "dev"],
    )
    
    # Retrieve and verify tags
    retrieved = store.get(memory.id)
    assert retrieved is not None
    assert "jetson" in retrieved.tags


def test_memory_store_delete(temp_memory_db: Path) -> None:
    """Test deleting a memory."""
    store = MemoryStore(temp_memory_db)
    
    # Create and delete
    memory = store.add_memory("note", "Temporary note", 1)
    assert store.get(memory.id) is not None
    
    success = store.delete_memory(memory.id)
    assert success is True
    assert store.get(memory.id) is None


def test_memory_store_all_memories(temp_memory_db: Path) -> None:
    """Test retrieving all memories."""
    store = MemoryStore(temp_memory_db)
    
    # Create multiple
    for i in range(5):
        store.add_memory("note", f"Memory {i}", 1)
    
    # Get all
    all_memories = store.recent(limit=100)
    assert len(all_memories) >= 5
