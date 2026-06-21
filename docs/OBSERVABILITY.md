# Observability

The bridge exposes lightweight local endpoints for health checks and monitoring.

## Health

```powershell
curl http://127.0.0.1:8088/healthz
```

Returns JSON with `ok`, latest reading state, count, uptime, and matrix status.

## Prometheus Metrics

```powershell
curl http://127.0.0.1:8088/metrics
```

Metrics include:

| Metric | Meaning |
| --- | --- |
| `edge_impact_readings_total` | Total readings processed since bridge start |
| `edge_impact_uptime_seconds` | Bridge process uptime |
| `edge_impact_latest_risk` | Latest risk score |
| `edge_impact_matrix_connected` | `1` when matrix serial output is connected |
| `edge_impact_status{status="..."}` | One-hot current status |

## Prometheus Scrape Example

```yaml
scrape_configs:
  - job_name: edge-impact-lab
    static_configs:
      - targets: ["jetson.local:8088"]
```

Use `127.0.0.1:8088` for local-only demos. Bind the bridge to `0.0.0.0` only on trusted lab networks.
