from __future__ import annotations

import argparse
import json
import logging
import os
import queue
import random
import signal
import sqlite3
import sys
import threading
import time
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    import serial
except ImportError as exc:  # pragma: no cover
    raise SystemExit("pyserial is required. Run: python -m pip install pyserial") from exc

from edge_lab.metrics import parse_sensor_line, score_reading
from edge_lab.mqtt import create_mqtt_publisher
from edge_lab.node import collect_node_snapshot
from edge_lab.risk_profile import RiskProfile, load_risk_profile

LOGGER = logging.getLogger("edge-impact")


@dataclass
class Reading:
    ts: float
    source: str
    payload: dict[str, Any]
    risk: int
    status: str
    reasons: list[str]


class LabState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.latest: Reading | None = None
        self.count = 0
        self.started_at = time.time()
        self.matrix_status = "UNKNOWN"

    def update(self, reading: Reading) -> None:
        with self._lock:
            self.latest = reading
            self.count += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            latest = asdict(self.latest) if self.latest else None
            return {
                "latest": latest,
                "count": self.count,
                "uptime_s": round(time.time() - self.started_at, 1),
                "matrix_status": self.matrix_status,
            }

    def set_matrix_status(self, status: str) -> None:
        with self._lock:
            self.matrix_status = status


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Edge Impact Lab serial bridge and dashboard.")
    parser.add_argument("--sensor-port", default=os.getenv("EDGE_LAB_SENSOR_PORT"))
    parser.add_argument("--matrix-port", default=os.getenv("EDGE_LAB_MATRIX_PORT"))
    parser.add_argument("--baud", type=int, default=int(os.getenv("EDGE_LAB_BAUD", "115200")))
    parser.add_argument("--db", default=os.getenv("EDGE_LAB_DB", "edge_lab.db"))
    parser.add_argument("--host", default=os.getenv("EDGE_LAB_HOST", "127.0.0.1"))
    parser.add_argument("--http-port", type=int, default=int(os.getenv("EDGE_LAB_HTTP_PORT", "8088")))
    parser.add_argument("--demo", action="store_true", help="Generate synthetic telemetry when hardware is not streaming.")
    parser.add_argument("--log-level", default=os.getenv("EDGE_LAB_LOG_LEVEL", "INFO"))
    parser.add_argument("--mqtt-host", default=os.getenv("EDGE_LAB_MQTT_HOST"))
    parser.add_argument("--mqtt-port", type=int, default=int(os.getenv("EDGE_LAB_MQTT_PORT", "1883")))
    parser.add_argument("--mqtt-topic", default=os.getenv("EDGE_LAB_MQTT_TOPIC", "edge-impact-lab"))
    parser.add_argument("--mqtt-client-id", default=os.getenv("EDGE_LAB_MQTT_CLIENT_ID", "edge-impact-jetson"))
    parser.add_argument("--mqtt-username", default=os.getenv("EDGE_LAB_MQTT_USERNAME"))
    parser.add_argument("--mqtt-password", default=os.getenv("EDGE_LAB_MQTT_PASSWORD"))
    parser.add_argument("--risk-profile", default=os.getenv("EDGE_LAB_RISK_PROFILE"))
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format="%(asctime)s %(levelname)s %(message)s")
    stop_event = threading.Event()
    signal.signal(signal.SIGINT, lambda _sig, _frame: stop_event.set())
    signal.signal(signal.SIGTERM, lambda _sig, _frame: stop_event.set())

    db_path = Path(args.db)
    init_db(db_path)
    risk_profile = load_risk_profile(args.risk_profile)
    LOGGER.info("Using risk profile %s", risk_profile.name)
    state = LabState()
    outbound: queue.Queue[str] = queue.Queue(maxsize=50)
    mqtt_publisher = create_mqtt_publisher(
        args.mqtt_host,
        args.mqtt_port,
        args.mqtt_topic,
        args.mqtt_client_id,
        args.mqtt_username,
        args.mqtt_password,
    )

    threads: list[threading.Thread] = []
    if args.sensor_port:
        threads.append(
            threading.Thread(
                target=read_sensor_loop,
                name="sensor-reader",
                args=(args.sensor_port, args.baud, db_path, state, outbound, mqtt_publisher, risk_profile, stop_event),
                daemon=True,
            )
        )
    else:
        LOGGER.warning("No sensor port configured; use --sensor-port or --demo.")

    if args.matrix_port:
        threads.append(
            threading.Thread(
                target=matrix_writer_loop,
                name="matrix-writer",
                args=(args.matrix_port, args.baud, state, outbound, stop_event),
                daemon=True,
            )
        )
    else:
        LOGGER.warning("No matrix port configured; status will only appear on the dashboard.")

    if args.demo:
        threads.append(
            threading.Thread(
                target=demo_loop,
                name="demo-generator",
                args=(db_path, state, outbound, mqtt_publisher, risk_profile, stop_event),
                daemon=True,
            )
        )

    for thread in threads:
        thread.start()

    server = make_server(args.host, args.http_port, db_path, state)
    LOGGER.info("Dashboard listening on http://%s:%s", args.host, args.http_port)
    while not stop_event.is_set():
        server.handle_request()

    mqtt_publisher.close()
    server.server_close()
    return 0


def read_sensor_loop(
    port: str,
    baud: int,
    db_path: Path,
    state: LabState,
    outbound: queue.Queue[str],
    mqtt_publisher: Any,
    risk_profile: RiskProfile,
    stop_event: threading.Event,
) -> None:
    while not stop_event.is_set():
        try:
            with serial.Serial(port, baud, timeout=1) as ser:
                LOGGER.info("Reading sensor telemetry from %s", port)
                while not stop_event.is_set():
                    raw = ser.readline()
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="replace")
                    payload = parse_sensor_line(line)
                    if payload is None:
                        continue
                    reading = build_reading(port, payload, risk_profile)
                    persist_reading(db_path, reading)
                    state.update(reading)
                    send_matrix_status(outbound, reading.status, reading.risk)
                    mqtt_publisher.publish_reading(reading)
        except (OSError, serial.SerialException) as exc:
            LOGGER.warning("Sensor port %s unavailable: %s", port, exc)
            stop_event.wait(3)


def matrix_writer_loop(
    port: str,
    baud: int,
    state: LabState,
    outbound: queue.Queue[str],
    stop_event: threading.Event,
) -> None:
    while not stop_event.is_set():
        try:
            with serial.Serial(port, baud, timeout=0.5, write_timeout=1) as ser:
                state.set_matrix_status("CONNECTED")
                LOGGER.info("Sending status to matrix on %s", port)
                while not stop_event.is_set():
                    try:
                        message = outbound.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    ser.write((message.strip() + "\n").encode("utf-8"))
                    ser.flush()
        except (OSError, serial.SerialException) as exc:
            state.set_matrix_status("DISCONNECTED")
            LOGGER.warning("Matrix port %s unavailable: %s", port, exc)
            stop_event.wait(3)


def demo_loop(
    db_path: Path,
    state: LabState,
    outbound: queue.Queue[str],
    mqtt_publisher: Any,
    risk_profile: RiskProfile,
    stop_event: threading.Event,
) -> None:
    while not stop_event.is_set():
        payload = {
            "temperature_c": round(random.uniform(29, 47), 2),
            "humidity_pct": round(random.uniform(38, 82), 2),
            "ax": round(random.uniform(-0.25, 0.25), 3),
            "ay": round(random.uniform(-0.25, 0.25), 3),
            "az": round(random.uniform(0.85, 1.85), 3),
            "sound_level": round(random.uniform(0.1, 0.9), 3),
            "demo": True,
        }
        reading = build_reading("demo", payload, risk_profile)
        persist_reading(db_path, reading)
        state.update(reading)
        send_matrix_status(outbound, reading.status, reading.risk)
        mqtt_publisher.publish_reading(reading)
        stop_event.wait(2)


def build_reading(source: str, payload: dict[str, Any], risk_profile: RiskProfile | None = None) -> Reading:
    result = score_reading(payload, risk_profile)
    return Reading(
        ts=time.time(),
        source=source,
        payload=payload,
        risk=result.score,
        status=result.status,
        reasons=result.reasons,
    )


def send_matrix_status(outbound: queue.Queue[str], status: str, risk: int) -> None:
    try:
        outbound.put_nowait(f"STATUS:{status}:{risk}")
    except queue.Full:
        pass


def init_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                source TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                risk INTEGER NOT NULL,
                status TEXT NOT NULL,
                reasons_json TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def persist_reading(path: Path, reading: Reading) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            INSERT INTO readings (ts, source, payload_json, risk, status, reasons_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                reading.ts,
                reading.source,
                json.dumps(reading.payload, sort_keys=True),
                reading.risk,
                reading.status,
                json.dumps(reading.reasons),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_history(path: Path, limit: int = 100) -> list[dict[str, Any]]:
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            """
            SELECT ts, source, payload_json, risk, status, reasons_json
            FROM readings
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "ts": ts,
            "source": source,
            "payload": json.loads(payload_json),
            "risk": risk,
            "status": status,
            "reasons": json.loads(reasons_json),
        }
        for ts, source, payload_json, risk, status, reasons_json in rows
    ]


def make_server(host: str, port: int, db_path: Path, state: LabState) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                self._send_text(DASHBOARD_HTML, "text/html; charset=utf-8")
            elif self.path == "/api/latest":
                self._send_json(state.snapshot())
            elif self.path.startswith("/api/history"):
                self._send_json({"history": fetch_history(db_path)})
            elif self.path == "/api/node":
                self._send_json(collect_node_snapshot())
            elif self.path == "/healthz":
                self._send_json({"ok": True, **state.snapshot()})
            elif self.path == "/metrics":
                self._send_text(render_prometheus_metrics(state), "text/plain; version=0.0.4; charset=utf-8")
            else:
                self.send_error(HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: Any) -> None:
            LOGGER.debug(format, *args)

        def _send_json(self, payload: dict[str, Any]) -> None:
            self._send_text(json.dumps(payload), "application/json")

        def _send_text(self, body: str, content_type: str) -> None:
            data = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer((host, port), Handler)
    server.timeout = 0.5
    return server


def render_prometheus_metrics(state: LabState) -> str:
    snapshot = state.snapshot()
    latest = snapshot["latest"] or {}
    status = latest.get("status", "WAITING")
    risk = latest.get("risk", 0)
    matrix_connected = 1 if snapshot["matrix_status"] == "CONNECTED" else 0
    statuses = ["OK", "WARN", "ALERT", "WAITING"]

    lines = [
        "# HELP edge_impact_readings_total Total telemetry readings processed.",
        "# TYPE edge_impact_readings_total counter",
        f"edge_impact_readings_total {snapshot['count']}",
        "# HELP edge_impact_uptime_seconds Bridge process uptime in seconds.",
        "# TYPE edge_impact_uptime_seconds gauge",
        f"edge_impact_uptime_seconds {snapshot['uptime_s']}",
        "# HELP edge_impact_latest_risk Latest calculated risk score.",
        "# TYPE edge_impact_latest_risk gauge",
        f"edge_impact_latest_risk {risk}",
        "# HELP edge_impact_matrix_connected Whether the matrix serial output is connected.",
        "# TYPE edge_impact_matrix_connected gauge",
        f"edge_impact_matrix_connected {matrix_connected}",
        "# HELP edge_impact_status Current status as one-hot labels.",
        "# TYPE edge_impact_status gauge",
    ]
    for possible_status in statuses:
        value = 1 if status == possible_status else 0
        lines.append(f'edge_impact_status{{status="{possible_status}"}} {value}')

    return "\n".join(lines) + "\n"


DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Edge Impact Lab</title>
<style>
body { margin: 0; font-family: Arial, sans-serif; background: #f5f7f8; color: #172026; }
main { max-width: 980px; margin: 0 auto; padding: 24px; }
h1 { font-size: 30px; margin: 0 0 16px; letter-spacing: 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
.card { background: #fff; border: 1px solid #dce2e5; border-radius: 8px; padding: 16px; }
.value { font-size: 34px; font-weight: 700; }
.ok { color: #087443; } .warn { color: #9a5b00; } .alert { color: #b42318; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #e8eef1; padding: 12px; border-radius: 8px; }
table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #dce2e5; }
td, th { padding: 8px; border-bottom: 1px solid #dce2e5; text-align: left; font-size: 14px; }
</style>
</head>
<body>
<main>
<h1>Edge Impact Lab</h1>
<section class="grid">
  <div class="card"><div>Status</div><div id="status" class="value">--</div></div>
  <div class="card"><div>Risk</div><div id="risk" class="value">--</div></div>
  <div class="card"><div>Readings</div><div id="count" class="value">--</div></div>
  <div class="card"><div>Matrix</div><div id="matrix" class="value">--</div></div>
  <div class="card"><div>Node</div><div id="node" class="value">--</div></div>
</section>
<section class="card" style="margin-top:12px"><h2>Latest Telemetry</h2><pre id="latest">{}</pre></section>
<section class="card" style="margin-top:12px"><h2>Jetson Readiness</h2><pre id="node-details">{}</pre></section>
<section style="margin-top:12px"><h2>Recent History</h2><table><thead><tr><th>Time</th><th>Source</th><th>Status</th><th>Risk</th><th>Reasons</th></tr></thead><tbody id="history"></tbody></table></section>
</main>
<script>
async function refresh() {
  const latest = await fetch('/api/latest').then(r => r.json());
  const history = await fetch('/api/history').then(r => r.json());
  const node = await fetch('/api/node').then(r => r.json());
  const reading = latest.latest || {};
  const status = reading.status || 'WAITING';
  const statusEl = document.getElementById('status');
  statusEl.textContent = status;
  statusEl.className = 'value ' + status.toLowerCase();
  document.getElementById('risk').textContent = reading.risk ?? '--';
  document.getElementById('count').textContent = latest.count;
  document.getElementById('matrix').textContent = latest.matrix_status;
  document.getElementById('node').textContent = node.hostname || 'unknown';
  document.getElementById('latest').textContent = JSON.stringify(reading.payload || {}, null, 2);
  document.getElementById('node-details').textContent = JSON.stringify(node, null, 2);
  document.getElementById('history').innerHTML = history.history.slice(0, 12).map(row => `
    <tr><td>${new Date(row.ts * 1000).toLocaleTimeString()}</td><td>${row.source}</td><td>${row.status}</td><td>${row.risk}</td><td>${row.reasons.join(', ')}</td></tr>
  `).join('');
}
refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
