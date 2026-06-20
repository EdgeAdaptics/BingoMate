# Security Notes

## Secrets

- Do not commit Wi-Fi passwords, OpenAI keys, GitHub tokens, SSH keys, or Jetson login passwords.
- Do not commit MQTT broker usernames, passwords, cloud connection strings, or device certificates.
- Use `.env`, `.env.local`, shell environment variables, or interactive prompts.
- `.gitignore` excludes `.env*` except `.env.example`.

## Serial Automation

`scripts/connect_jetson_wifi_serial.py` sends commands only after an interactive Jetson login. It prompts for the Jetson login password and Wi-Fi password when environment variables are not set.

## Local Dashboard

The default dashboard bind address is `127.0.0.1`. On Jetson, use `--host 0.0.0.0` only on trusted lab networks.

## Service Hardening Backlog

- Add a dedicated Linux service user.
- Add systemd sandboxing options after hardware access paths are finalized.
- Add log rotation for long-running demos.
- Add TLS or reverse proxy protection before exposing outside the lab.
- Treat risk profile changes as operational configuration and review them before field demos.
