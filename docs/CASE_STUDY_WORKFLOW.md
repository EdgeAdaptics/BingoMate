# Case Study Workflow

Use this workflow to turn the lab into a portfolio artifact after a demo session.

## Collect

Run with hardware or demo mode:

```powershell
edge-impact-doctor --format markdown --out exports\doctor.md
edge-impact-bridge --demo
```

For deterministic data:

```powershell
edge-impact-seed-demo --db edge_lab.db --all
```

## Export

```powershell
edge-impact-export --db edge_lab.db --format csv --out exports\readings.csv
edge-impact-export --db edge_lab.db --format jsonl --out exports\readings.jsonl
```

## Summarize

```powershell
edge-impact-report --db edge_lab.db --format markdown --out exports\summary.md
edge-impact-report --db edge_lab.db --format json --out exports\summary.json
```

## Portfolio Notes

Capture these points in a README update, blog post, or interview story:

- What physical device produced the signal.
- What the Jetson decided locally.
- What the matrix displayed.
- What the report showed after the run.
- What would be improved with more data.

## Strong Evidence

- `exports/readings.csv` shows raw telemetry.
- `exports/summary.md` shows operational interpretation.
- `exports/doctor.md` shows lab readiness.
- A screenshot shows the dashboard.
- A photo or short video shows the physical matrix output.
