"""Tests for the devices module."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from bingomate.devices import DeviceRegistry, DeviceStore


@pytest.fixture
def temp_devices_db() -> Path:
    """Create a temporary devices database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_devices.db"
        yield db_path


def test_device_registry_init(temp_devices_db: Path) -> None:
    """Test device registry initialization."""
    store = DeviceStore(temp_devices_db)
    registry = DeviceRegistry(store)
    assert registry is not None


def test_device_registry_seed_simulated(temp_devices_db: Path) -> None:
    """Test seeding simulated devices."""
    store = DeviceStore(temp_devices_db)
    registry = DeviceRegistry(store)
    
    registry.seed_simulated_devices()
    devices = registry.list_devices()
    
    assert len(devices) > 0


def test_device_registry_encryption_status(temp_devices_db: Path) -> None:
    """Test device encryption status."""
    store = DeviceStore(temp_devices_db)
    registry = DeviceRegistry(store)
    
    # Without cipher
    assert registry.encryption_enabled is False
