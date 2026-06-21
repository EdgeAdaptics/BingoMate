# BingoMate Development Guide

## Getting Started

### Setup

1. **Create Python Virtual Environment**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

2. **Install Project with Dev Dependencies**
```powershell
python -m pip install -e ".[mqtt,ble,cloud]"
python -m pip install pytest pytest-asyncio requests
```

3. **Verify Installation**
```powershell
python scripts/preflight_publish.py  # Security checks
python scripts/self_test.py          # Core functionality
```

## Running the API Server

### Local Development
```powershell
python -m bingomate.cli --host 127.0.0.1 --port 8090
```

### With Optional Features
```powershell
# Enable local LLM (requires Ollama or similar running)
python -m bingomate.cli \
  --local-llm-enabled \
  --local-llm-url http://127.0.0.1:11434/v1 \
  --local-llm-model llama2

# Enable STT
python -m bingomate.cli \
  --stt-enabled \
  --stt-provider openai-compatible \
  --stt-url http://127.0.0.1:8000/v1 \
  --stt-model whisper-1

# Enable Camera
python -m bingomate.cli --camera-enabled
```

## Development Utilities

Use the dev_utils script for common development tasks:

```powershell
# Health check
python scripts/dev_utils.py health-check

# Test all APIs
python scripts/dev_utils.py test-api

# Seed sample memories
python scripts/dev_utils.py seed-memories

# Load sample automation policies
python scripts/dev_utils.py load-policies

# Test voice simulation
python scripts/dev_utils.py test-voice

# Test vision simulation
python scripts/dev_utils.py test-vision
```

## Running Tests

### Unit Tests
```powershell
pytest tests/ -v
```

### Specific Test Module
```powershell
pytest tests/test_memory.py -v
pytest tests/test_reasoning.py -v
pytest tests/test_automation.py -v
```

### With Coverage
```powershell
pip install pytest-cov
pytest tests/ --cov=bingomate --cov-report=html
```

## API Testing

### Using curl
```powershell
# Health check
curl http://127.0.0.1:8090/healthz

# Create memory
curl -X POST http://127.0.0.1:8090/api/memories `
  -H "Content-Type: application/json" `
  -d '{
    "kind": "note",
    "content": "Test memory",
    "importance": 1,
    "tags": ["test"]
  }'

# Get reasoning status
curl http://127.0.0.1:8090/api/reasoning/status

# List memories
curl "http://127.0.0.1:8090/api/memories?q=test&limit=10"
```

### Using Python Requests
```python
import requests

# Health check
r = requests.get("http://127.0.0.1:8090/healthz")
print(r.json())

# Create memory
r = requests.post("http://127.0.0.1:8090/api/memories", json={
    "kind": "note",
    "content": "My development note",
    "importance": 1
})
print(r.json())

# Reasoning probe
r = requests.post("http://127.0.0.1:8090/api/reasoning/probe", json={
    "prompt": "What can you do?",
    "include_memories": True
})
print(r.json()["response"]["response"])
```

## Editing Code

### Adding a New Skill
Create a new skill class in `bingomate/skills/` and register it:

```python
from bingomate.skills import Skill, SkillResult

class MySkill:
    name = "my_skill"
    description = "My custom skill"
    source = "custom"
    requires_approval = False
    
    def run(self, prompt: str, context: dict) -> SkillResult:
        # Implement skill logic
        return SkillResult(True, "Success", {"result": "..."})
```

### Adding an API Endpoint
Add to `bingomate/api/app.py`:

```python
@app.get("/api/custom/endpoint")
def my_endpoint(param: str = "", _auth: None = Depends(require_auth)) -> dict:
    events.publish("custom.event", {"param": param})
    return {"result": "Success"}
```

### Adding Memory Types
Extend `bingomate/memory/store.py` with new memory kinds:

```python
# In memory.create():
if kind not in {"note", "reminder", "observation", "your_kind"}:
    kind = "note"
```

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Database Contents
```powershell
# Query memory database
sqlite3 data/bingomate.db "SELECT id, kind, content FROM memory LIMIT 5;"

# Query devices database
sqlite3 data/bingomate_devices.db "SELECT device_id, name FROM devices;"
```

### Mock HTTP Responses
```python
# In tests, use requests-mock
import requests_mock

with requests_mock.Mocker() as m:
    m.get("http://127.0.0.1:8090/api/status", json={"ok": True})
    resp = requests.get("http://127.0.0.1:8090/api/status")
    assert resp.json()["ok"]
```

## Code Style

- Use type hints everywhere
- Follow PEP 8
- Use dataclasses for data structures
- Prefer functional patterns
- Keep functions small and focused

### Format Code
```powershell
pip install black isort
black bingomate tests scripts
isort bingomate tests scripts
```

## Common Tasks

### Add a New Configuration Option
1. Add to `BingoMateSettings` dataclass in `bingomate/core.py`
2. Add CLI argument in `bingomate/cli.py`
3. Update `default_settings()` in `bingomate/core.py`
4. Pass to relevant module

### Add Database Migration
SQLite migration strategy:
1. Create new table with `_v2` suffix
2. Copy and transform data
3. Drop old table
4. Rename new table

### Test End-to-End Flow
```powershell
# 1. Start server
python -m bingomate.cli

# 2. In another terminal
python -c "
import requests
import json

# Create memory
r = requests.post('http://127.0.0.1:8090/api/memories',
    json={'kind': 'note', 'content': 'test'})
print('Memory created:', r.json())

# Reason with memory
r = requests.post('http://127.0.0.1:8090/api/reasoning/probe',
    json={'prompt': 'What do you know?', 'include_memories': True})
print('Reasoning:', r.json()['response']['response'])
"
```

## Publishing Changes

1. **Run all checks**
```powershell
python -m py_compile bingomate edge_lab scripts
python scripts/self_test.py
python scripts/preflight_publish.py
pytest tests/
```

2. **Create pull request**
```powershell
git checkout -b feature/my-feature
git add .
git commit -m "Description of changes"
git push origin feature/my-feature
```

## Resources

- **API Documentation**: `docs/API_ENDPOINTS.md`
- **Architecture**: `docs/BINGOMATE_ARCHITECTURE.md`
- **Setup Guide**: `docs/BINGOMATE_SETUP.md`
- **Roadmap**: `docs/TECHNICAL_ROADMAP.md`
- **Product Vision**: `docs/PRODUCT_VISION.md`

## Troubleshooting

### Import Errors
- Ensure `.venv` is activated
- Run `python -m pip install -e .` in project root

### Database Locked
- Close any open connections
- Delete `.db-shm` and `.db-wal` files
- Restart server

### API Port Already in Use
- Change port: `--port 8091`
- Or kill existing process: `Get-Process python | Stop-Process`

### Tests Failing
- Run `pytest -v` for detailed output
- Check `tests/conftest.py` for fixtures
- Ensure all dependencies installed
