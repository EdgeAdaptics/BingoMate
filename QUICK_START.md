# Quick Start Guide for BingoMate Development

## 30-Second Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[mqtt,ble,cloud]"
python -m pip install pytest
python -m bingomate.cli
```

Open `http://127.0.0.1:8090`.

## Five-Minute Verification

```powershell
python scripts/dev_utils.py health-check
python scripts/dev_utils.py test-api
python -m pytest tests -q
```

## Common Commands

### Start API

```powershell
python -m bingomate.cli --host 127.0.0.1 --port 8090
```

### Run Tests

```powershell
python -m pytest tests -v
python -m pytest tests/test_memory.py -v
```

### Core API Checks

```powershell
curl http://127.0.0.1:8090/healthz
curl http://127.0.0.1:8090/api/reasoning/status
curl http://127.0.0.1:8090/api/voice/stt/status
curl http://127.0.0.1:8090/api/automations/status
```

### Create Memory

```powershell
curl -X POST http://127.0.0.1:8090/api/memories `
  -H "Content-Type: application/json" `
  -d '{"kind":"note","content":"Test","importance":1}'
```

### Create Automation Policy

```powershell
curl -X POST http://127.0.0.1:8090/api/automations/policies `
  -H "Content-Type: application/json" `
  -d '{"trigger":"device_online","action":"notify_user","approved":false}'
```

## Project Structure

```text
bingomate/              Main package
  api/                  FastAPI application
  automation/           Automation policies
  devices/              Device management
  identity/             Assistant identity
  memory/               Memory storage and search
  reasoning/            AI reasoning engine
  security/             Auth and encryption
  skills/               Skill registry
  vision/               Vision analysis
  voice/                Voice pipeline

apps/                   Dashboard and Bingo display
docs/                   Product, setup, and API documentation
firmware/               ESP32 and Arduino integration sketches
scripts/                Setup, validation, and dev utilities
tests/                  Unit test suite
```

## Key Files

| File | Purpose |
| --- | --- |
| `bingomate/api/app.py` | FastAPI app and endpoints |
| `bingomate/core.py` | Settings and configuration |
| `bingomate/cli.py` | Command-line interface |
| `bingomate/skills/bingo_personality.py` | Bingo personality skills |
| `scripts/dev_utils.py` | Local development helper |
| `docs/API_ENDPOINTS.md` | API reference |
| `docs/DEVELOPMENT.md` | Development guide |
| `docs/BINGOMATE_SETUP.md` | Setup guide |

## New In This Readiness Pass

- Test suite covering core modules.
- Automation policies with CRUD, approval, execution, and audit log support.
- API documentation and development guide.
- Development utility script with no third-party request dependency.
- Bingo-native personality skills.
- Neutral Git publishing branch: `edgeadaptics/bingomate-product-scaffold`.

## Troubleshooting

### API Will Not Start

```powershell
Get-Process python
Stop-Process -Name python
python -m bingomate.cli --port 8091
```

### Import Errors

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

### Reset Local Databases

```powershell
Remove-Item data\*.db,data\*.db-shm,data\*.db-wal -ErrorAction SilentlyContinue
python -m bingomate.cli
```

## Next Steps

1. Read `docs/PRODUCT_VISION.md`.
2. Review `docs/BINGOMATE_ARCHITECTURE.md`.
3. Start the API with `python -m bingomate.cli`.
4. Run `python scripts/dev_utils.py test-api`.
5. Validate hardware on the Jetson.
