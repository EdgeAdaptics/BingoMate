from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BingoMateSettings:
    data_dir: Path = Path("data")
    memory_db: Path = Path("data/bingomate.db")
    skills_db: Path = Path("data/bingomate_skills.db")
    devices_db: Path = Path("data/bingomate_devices.db")
    dashboard_dir: Path = Path("apps/dashboard")
    display_dir: Path = Path("apps/bingo_display")
    assistant_name: str = "Bingo"
    host: str = "127.0.0.1"
    port: int = 8090
    simulation: bool = True
    cloud_assist: bool = False
    openai_model: str = ""
    local_llm_enabled: bool = False
    local_llm_url: str = ""
    local_llm_model: str = ""
    local_llm_provider: str = "openai-compatible"
    local_llm_timeout_seconds: float = 20.0
    local_llm_max_tokens: int = 512
    auth_token: str = ""
    memory_key: str = ""
    device_key: str = ""
    stt_enabled: bool = False
    stt_provider: str = "openai-compatible"
    stt_url: str = ""
    stt_model: str = ""
    stt_command: str = ""
    stt_timeout_seconds: float = 30.0
    camera_enabled: bool = False
    camera_index: int = 0
    mqtt_host: str = ""
    mqtt_port: int = 1883
    mqtt_topic: str = "bingomate/devices"
    mqtt_username: str = ""
    mqtt_password: str = ""
    ble_enabled: bool = False


def default_settings() -> BingoMateSettings:
    return BingoMateSettings(
        data_dir=Path(os.getenv("BINGOMATE_DATA_DIR", "data")),
        memory_db=Path(os.getenv("BINGOMATE_MEMORY_DB", "data/bingomate.db")),
        skills_db=Path(os.getenv("BINGOMATE_SKILLS_DB", "data/bingomate_skills.db")),
        devices_db=Path(os.getenv("BINGOMATE_DEVICES_DB", "data/bingomate_devices.db")),
        dashboard_dir=Path(os.getenv("BINGOMATE_DASHBOARD_DIR", "apps/dashboard")),
        display_dir=Path(os.getenv("BINGOMATE_DISPLAY_DIR", "apps/bingo_display")),
        host=os.getenv("BINGOMATE_HOST", "127.0.0.1"),
        port=int(os.getenv("BINGOMATE_PORT", "8090")),
        cloud_assist=os.getenv("BINGOMATE_CLOUD_ASSIST", "0") == "1",
        openai_model=os.getenv("BINGOMATE_OPENAI_MODEL", ""),
        local_llm_enabled=os.getenv("BINGOMATE_LOCAL_LLM_ENABLED", "0") == "1",
        local_llm_url=os.getenv("BINGOMATE_LOCAL_LLM_URL", ""),
        local_llm_model=os.getenv("BINGOMATE_LOCAL_LLM_MODEL", ""),
        local_llm_provider=os.getenv("BINGOMATE_LOCAL_LLM_PROVIDER", "openai-compatible"),
        local_llm_timeout_seconds=float(os.getenv("BINGOMATE_LOCAL_LLM_TIMEOUT_SECONDS", "20")),
        local_llm_max_tokens=int(os.getenv("BINGOMATE_LOCAL_LLM_MAX_TOKENS", "512")),
        auth_token=os.getenv("BINGOMATE_AUTH_TOKEN", ""),
        memory_key=os.getenv("BINGOMATE_MEMORY_KEY", ""),
        device_key=os.getenv("BINGOMATE_DEVICE_KEY", os.getenv("BINGOMATE_MEMORY_KEY", "")),
        stt_enabled=os.getenv("BINGOMATE_STT_ENABLED", "0") == "1",
        stt_provider=os.getenv("BINGOMATE_STT_PROVIDER", "openai-compatible"),
        stt_url=os.getenv("BINGOMATE_STT_URL", ""),
        stt_model=os.getenv("BINGOMATE_STT_MODEL", ""),
        stt_command=os.getenv("BINGOMATE_STT_COMMAND", ""),
        stt_timeout_seconds=float(os.getenv("BINGOMATE_STT_TIMEOUT_SECONDS", "30")),
        camera_enabled=os.getenv("BINGOMATE_CAMERA_ENABLED", "0") == "1",
        camera_index=int(os.getenv("BINGOMATE_CAMERA_INDEX", "0")),
        mqtt_host=os.getenv("BINGOMATE_MQTT_HOST", ""),
        mqtt_port=int(os.getenv("BINGOMATE_MQTT_PORT", "1883")),
        mqtt_topic=os.getenv("BINGOMATE_MQTT_TOPIC", "bingomate/devices"),
        mqtt_username=os.getenv("BINGOMATE_MQTT_USERNAME", ""),
        mqtt_password=os.getenv("BINGOMATE_MQTT_PASSWORD", ""),
        ble_enabled=os.getenv("BINGOMATE_BLE_ENABLED", "0") == "1",
    )


def ensure_data_dir(settings: BingoMateSettings) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.memory_db.parent.mkdir(parents=True, exist_ok=True)
    settings.skills_db.parent.mkdir(parents=True, exist_ok=True)
    settings.devices_db.parent.mkdir(parents=True, exist_ok=True)
