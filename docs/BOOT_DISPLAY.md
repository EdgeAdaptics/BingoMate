# BingoMate Boot Display

## Goal

The boot display turns a monitor connected to the Jetson into Bingo's always-on presence:

- Full-screen animated 3D-style Bingo character.
- Local looping GIF avatar from `/display/assets/bingo-boot.gif`.
- Local startup chime from `/api/voice/startup.wav`.
- Browser speech synthesis for "Bingo online" voice.
- Visible boot sequence for brain, memory, device trust, voice, and presence readiness.
- Live identity, context, device, skill, and proactive suggestion state.
- Kiosk launch when the Jetson reaches graphical boot.

The character is original and code-native. It does not use copyrighted movie clips, Weebo assets, or copied character design.

## Manual Run

Start the API:

```bash
source .venv/bin/activate
bingomate-api --host 127.0.0.1 --port 8090
```

Open the display:

```text
http://127.0.0.1:8090/display
```

The browser may block audio until a click unless Chromium is started with:

```bash
--autoplay-policy=no-user-gesture-required
```

## Jetson Boot-To-Bingo

Prerequisites:

- Jetson boots into a graphical desktop session.
- A monitor or HDMI display is attached.
- Chromium is installed as `chromium-browser` or `chromium`.
- `scripts/jetson_prepare.sh` has created `.venv`.

Install the API and display services:

```bash
bash scripts/install_bingomate_display_service.sh
```

This creates:

- `bingomate-api.service` for the FastAPI backend.
- `bingomate-display.service` for Chromium kiosk mode.

Useful service commands:

```bash
sudo systemctl status bingomate-api.service --no-pager
sudo systemctl status bingomate-display.service --no-pager
sudo journalctl -u bingomate-display.service -f
sudo systemctl restart bingomate-display.service
```

## Local Token Handling

For a physical display connected to the Jetson, prefer:

```bash
BINGOMATE_HOST=127.0.0.1
```

If `BINGOMATE_AUTH_TOKEN` is enabled, the display can read a local token from the URL hash without sending it to the server logs:

```bash
BINGOMATE_DISPLAY_TOKEN="same-local-token"
```

The kiosk launcher converts that into:

```text
http://127.0.0.1:8090/display#token=same-local-token
```

The display stores the token in browser local storage and then removes it from the visible URL.

## Local Avatar Asset

The first boot avatar is a generated local GIF committed under `apps/bingo_display/assets/bingo-boot.gif`. It is served only through `/display/assets/{asset}` with path traversal protection. The large central character remains CSS 3D so the display works offline without a frontend build or WebGL dependency.

## Audio Behavior

- `/api/voice/startup.wav` returns a generated local WAV chime.
- `/api/voice/startup` returns the startup phrase.
- The display uses Web Speech API for the voice when the browser supports it.
- Kiosk mode allows startup sound immediately; ordinary browsers may require clicking **Replay startup voice**.

## Future 3D Path

The first display is CSS 3D so it runs offline with no GPU-heavy frontend stack. Future upgrades can replace the character layer while keeping the same API:

- WebGL/Three.js avatar.
- Live mouth shapes from local TTS timing.
- Camera-aware gaze direction.
- ESP32 matrix mirrored mood states.
- Jetson-accelerated local voice and vision state transitions.
