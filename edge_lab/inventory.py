from __future__ import annotations

import argparse
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pyserial is required. Run: python -m pip install pyserial") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="List and optionally probe serial devices.")
    parser.add_argument("--probe", action="store_true", help="Open each port at 115200 and read briefly.")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--seconds", type=float, default=1.5)
    args = parser.parse_args()

    ports = list(list_ports.comports())
    if not ports:
        print("No serial ports detected.")
        return 1

    for port in ports:
        print(f"{port.device}\t{port.description}\t{port.hwid}")
        if args.probe:
            sample = probe_port(port.device, args.baud, args.seconds)
            if sample:
                print(sample)
            else:
                print("(no serial text)")

    return 0


def probe_port(device: str, baud: int, seconds: float) -> str:
    try:
        with serial.Serial(device, baud, timeout=0.2, write_timeout=0.2) as ser:
            time.sleep(0.3)
            ser.write(b"\r\n")
            ser.flush()
            deadline = time.time() + seconds
            chunks: list[bytes] = []
            while time.time() < deadline:
                waiting = ser.in_waiting
                if waiting:
                    chunks.append(ser.read(waiting))
                time.sleep(0.05)
    except (OSError, serial.SerialException) as exc:
        return f"(probe failed: {exc})"

    return b"".join(chunks).decode("utf-8", errors="replace").strip()


if __name__ == "__main__":
    sys.exit(main())
