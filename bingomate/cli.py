from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bingomate.core import BingoMateSettings, default_settings


def main() -> int:
    defaults = default_settings()
    parser = argparse.ArgumentParser(description="Run BingoMate backend services.")
    parser.add_argument("--host", default=defaults.host)
    parser.add_argument("--port", type=int, default=defaults.port)
    parser.add_argument("--data-dir", default=str(defaults.data_dir))
    parser.add_argument("--memory-db", default=str(defaults.memory_db))
    parser.add_argument("--skills-db", default=str(defaults.skills_db))
    parser.add_argument("--devices-db", default=str(defaults.devices_db))
    parser.add_argument("--dashboard-dir", default=str(defaults.dashboard_dir))
    parser.add_argument("--display-dir", default=str(defaults.display_dir))
    parser.add_argument("--cloud-assist", action="store_true", default=defaults.cloud_assist)
    parser.add_argument("--openai-model", default=defaults.openai_model)
    parser.add_argument("--local-llm-enabled", action="store_true", default=defaults.local_llm_enabled)
    parser.add_argument("--local-llm-url", default=defaults.local_llm_url)
    parser.add_argument("--local-llm-model", default=defaults.local_llm_model)
    parser.add_argument("--local-llm-provider", choices=["openai-compatible", "ollama"], default=defaults.local_llm_provider)
    parser.add_argument("--local-llm-timeout-seconds", type=float, default=defaults.local_llm_timeout_seconds)
    parser.add_argument("--local-llm-max-tokens", type=int, default=defaults.local_llm_max_tokens)
    parser.add_argument("--auth-token", default=defaults.auth_token)
    parser.add_argument("--stt-enabled", action="store_true", default=defaults.stt_enabled)
    parser.add_argument("--stt-provider", choices=["openai-compatible", "command"], default=defaults.stt_provider)
    parser.add_argument("--stt-url", default=defaults.stt_url)
    parser.add_argument("--stt-model", default=defaults.stt_model)
    parser.add_argument("--stt-command", default=defaults.stt_command)
    parser.add_argument("--stt-timeout-seconds", type=float, default=defaults.stt_timeout_seconds)
    parser.add_argument("--camera-enabled", action="store_true", default=defaults.camera_enabled)
    parser.add_argument("--camera-index", type=int, default=defaults.camera_index)
    parser.add_argument("--mqtt-host", default=defaults.mqtt_host)
    parser.add_argument("--mqtt-port", type=int, default=defaults.mqtt_port)
    parser.add_argument("--mqtt-topic", default=defaults.mqtt_topic)
    parser.add_argument("--mqtt-username", default=defaults.mqtt_username)
    parser.add_argument("--mqtt-password", default=defaults.mqtt_password)
    parser.add_argument("--ble-enabled", action="store_true", default=defaults.ble_enabled)
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("Install API dependencies with: python -m pip install -e .") from exc

    settings = BingoMateSettings(
        data_dir=Path(args.data_dir),
        memory_db=Path(args.memory_db),
        skills_db=Path(args.skills_db),
        devices_db=Path(args.devices_db),
        dashboard_dir=Path(args.dashboard_dir),
        display_dir=Path(args.display_dir),
        host=args.host,
        port=args.port,
        cloud_assist=args.cloud_assist,
        openai_model=args.openai_model,
        local_llm_enabled=args.local_llm_enabled,
        local_llm_url=args.local_llm_url,
        local_llm_model=args.local_llm_model,
        local_llm_provider=args.local_llm_provider,
        local_llm_timeout_seconds=args.local_llm_timeout_seconds,
        local_llm_max_tokens=args.local_llm_max_tokens,
        auth_token=args.auth_token,
        memory_key=defaults.memory_key,
        device_key=defaults.device_key,
        stt_enabled=args.stt_enabled,
        stt_provider=args.stt_provider,
        stt_url=args.stt_url,
        stt_model=args.stt_model,
        stt_command=args.stt_command,
        stt_timeout_seconds=args.stt_timeout_seconds,
        camera_enabled=args.camera_enabled,
        camera_index=args.camera_index,
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port,
        mqtt_topic=args.mqtt_topic,
        mqtt_username=args.mqtt_username,
        mqtt_password=args.mqtt_password,
        ble_enabled=args.ble_enabled,
    )

    from bingomate.api.app import create_app

    uvicorn.run(create_app(settings), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
