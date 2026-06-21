# BingoMate Security Model

## Security Principles

- Private by default.
- Local action before cloud action.
- Human approval before physical or sensitive action.
- Secrets never committed.
- Devices registered before trusted.
- System health and privacy state visible to the user.

## Threat Model

| Threat | Risk | Initial Control |
| --- | --- | --- |
| Committed secrets | Wi-Fi, API keys, or tokens leak publicly | `.gitignore`, `.env.example`, preflight scan |
| Unauthorized dashboard access | Private memories exposed on LAN | Bind to `127.0.0.1` by default; optional bearer token auth |
| Unsafe physical automation | Assistant controls devices unexpectedly | Permission policy blocks device actions |
| Rogue device messages | Fake ESP32 or sensor data | HMAC-signed messages for registered devices with persistent replay protection |
| Cloud data exposure | Memories sent to external APIs | Cloud paths opt-in only |
| Local device theft | Memory or device trust databases readable from disk | Optional encrypted memory content, metadata, conversation turns, and derived device HMAC keys |

## Current Controls

- No API keys or Wi-Fi passwords are stored in tracked files.
- Dashboard/API default to localhost.
- Protected API endpoints require `BINGOMATE_AUTH_TOKEN` when configured.
- Registered device messages use per-device shared secrets, derived HMAC keys, HMAC-SHA256 signatures, timestamp windows, and persisted nonce replay checks.
- Registered device trust persists locally in SQLite so ESP32, Arduino, and gateway registrations survive API restart.
- Derived device HMAC keys are encrypted at rest when `BINGOMATE_DEVICE_KEY` is configured.
- Sensitive device metadata keys such as passwords, tokens, credentials, API keys, and private keys are redacted before storage.
- Memory content, memory metadata, and conversation turns are encrypted at rest when `BINGOMATE_MEMORY_KEY` is configured.
- Automation proposals require approval for physical actions.
- Memory is local SQLite.
- Publishing preflight scans for common secret formats.

## Roadmap Controls

- Stronger key management backed by OS keyrings or Jetson fTPM.
- Device certificates and fTPM-backed device identity.
- Device key rotation and trust-on-first-use approval UX.
- Jetson fTPM-backed identity and attestation.
- Audit log for automation proposals, approvals, and executions.

## Operator Rules

- Do not run public-facing services without auth and TLS.
- Do not enable cloud APIs for private memory by default.
- Do not give BingoMate blanket permission for physical control.
- Do not lose `BINGOMATE_MEMORY_KEY`; encrypted rows cannot be recovered without it.
- Do not lose `BINGOMATE_DEVICE_KEY`; encrypted persisted device HMAC keys cannot be verified without it.
- Review generated shell commands before running them on Jetson.
