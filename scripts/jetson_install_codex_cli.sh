#!/usr/bin/env bash
set -euo pipefail

echo "==> BingoMate Jetson Codex CLI setup"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This installer is intended for Jetson Linux. Current OS: $(uname -s)"
fi

ARCH="$(uname -m)"
if [[ "${ARCH}" != "aarch64" && "${ARCH}" != "arm64" ]]; then
  echo "Warning: expected Jetson ARM64/aarch64, detected ${ARCH}."
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "Installing curl and certificates..."
  sudo apt-get update
  sudo apt-get install -y curl ca-certificates
fi

if command -v codex >/dev/null 2>&1; then
  echo "Codex CLI already installed: $(codex --version 2>/dev/null || echo installed)"
else
  echo "Installing Codex CLI from the official standalone installer..."
  CODEX_NON_INTERACTIVE=1 curl -fsSL https://chatgpt.com/codex/install.sh | sh
fi

mkdir -p "${HOME}/.codex"
CONFIG="${HOME}/.codex/config.toml"
if [[ ! -f "${CONFIG}" ]]; then
  cat > "${CONFIG}" <<'EOF'
approval_policy = "on-request"
sandbox_mode = "workspace-write"
cli_auth_credentials_store = "auto"
EOF
  chmod 600 "${CONFIG}"
  echo "Created ${CONFIG} with safe local defaults."
fi

if ! command -v codex >/dev/null 2>&1; then
  cat <<'EOF'
Codex was installed, but the command was not found on PATH.
Restart the shell, then check these common paths:
  export PATH="$HOME/.local/bin:$HOME/.codex/bin:$PATH"
EOF
  exit 1
fi

echo "==> Codex CLI version"
codex --version || true

cat <<'EOF'

Next steps:
  codex login
  codex doctor
  cd ~/BingoMate
  codex "Inspect this repo and propose the next Jetson setup step."

Do not commit ~/.codex, API keys, access tokens, or copied auth files.
EOF
