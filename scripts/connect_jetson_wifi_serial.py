from __future__ import annotations

import argparse
import getpass
import os
import shlex
import sys
import time

import serial


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure Jetson Wi-Fi through a serial login shell.")
    parser.add_argument("--port", default=os.getenv("JETSON_SERIAL_PORT", "COM3"))
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--ssid", default=os.getenv("LAB_WIFI_SSID", "simple_reuse"))
    parser.add_argument("--wifi-password", default=os.getenv("LAB_WIFI_PASSWORD"))
    parser.add_argument("--username", default=os.getenv("JETSON_USERNAME"))
    args = parser.parse_args()

    username = args.username or input("Jetson username: ").strip()
    login_password = getpass.getpass("Jetson login password: ")
    wifi_password = args.wifi_password or getpass.getpass("Wi-Fi password: ")

    commands = [
        ("export HISTCONTROL=ignorespace", "export HISTCONTROL=ignorespace"),
        ("nmcli radio wifi on", "nmcli radio wifi on"),
        (
            f"nmcli dev wifi connect {shlex.quote(args.ssid)} password <hidden>",
            f" nmcli dev wifi connect {shlex.quote(args.ssid)} password {shlex.quote(wifi_password)}",
        ),
        ("hostname -I", "hostname -I"),
    ]

    with serial.Serial(args.port, args.baud, timeout=0.5, write_timeout=1) as ser:
        print(f"Connected to {args.port}. Logging in as {username}.")
        send_line(ser, "")
        wait_for(ser, "login:", 20)
        send_line(ser, username)
        wait_for(ser, "Password:", 20)
        send_line(ser, login_password)
        time.sleep(2)
        for display, command in commands:
            print(f"$ {display}")
            send_line(ser, command)
            print(read_for(ser, 5))

    return 0


def send_line(ser: serial.Serial, line: str) -> None:
    ser.write((line + "\n").encode("utf-8"))
    ser.flush()


def wait_for(ser: serial.Serial, expected: str, seconds: int) -> None:
    deadline = time.time() + seconds
    buffer = ""
    while time.time() < deadline:
        buffer += ser.read(512).decode("utf-8", errors="replace")
        if expected in buffer:
            return
    raise TimeoutError(f"Did not see {expected!r}. Last output: {buffer[-500:]}")


def read_for(ser: serial.Serial, seconds: float) -> str:
    deadline = time.time() + seconds
    chunks: list[str] = []
    while time.time() < deadline:
        data = ser.read(512)
        if data:
            chunks.append(data.decode("utf-8", errors="replace"))
        time.sleep(0.1)
    return "".join(chunks).strip()


if __name__ == "__main__":
    sys.exit(main())
