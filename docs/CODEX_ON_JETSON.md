# Codex CLI On Jetson

Codex CLI can make the Jetson easier to operate because it lets the device inspect, edit, test, and explain its own repo from the terminal. Use it as a local engineering copilot, not as a secret store.

## Install

Run this on the Jetson after Wi-Fi is configured:

```bash
bash scripts/jetson_install_codex_cli.sh
```

The script uses the official Linux/macOS standalone installer:

```bash
CODEX_NON_INTERACTIVE=1 curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

## Login

Use one of the supported Codex auth paths:

```bash
codex login
codex doctor
```

Do not commit `~/.codex`, API keys, access tokens, or copied auth files.

## Useful Jetson Commands

```bash
cd ~/BingoMate
codex "Inspect this repo and propose the next Jetson setup step."
codex exec "Run python scripts/self_test.py and summarize failures."
codex doctor
```

## Safety Defaults

- Keep sandboxing enabled unless you are intentionally doing system setup.
- Prefer repository-scoped prompts.
- Do not expose `codex app-server` outside trusted local networks.
- Treat generated shell commands like production maintenance steps: inspect before running.
