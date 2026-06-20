from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class LocalLLMConfig:
    enabled: bool = False
    provider: str = "openai-compatible"
    endpoint: str = ""
    model: str = ""
    timeout_seconds: float = 20.0
    max_tokens: int = 512


class LocalLLMAdapter:
    def __init__(self, config: LocalLLMConfig) -> None:
        provider = config.provider.strip().lower()
        if provider not in {"openai-compatible", "ollama"}:
            provider = "openai-compatible"
        self.config = LocalLLMConfig(
            enabled=config.enabled,
            provider=provider,
            endpoint=config.endpoint.strip(),
            model=config.model.strip(),
            timeout_seconds=min(max(float(config.timeout_seconds), 1.0), 300.0),
            max_tokens=min(max(int(config.max_tokens), 16), 4096),
        )

    @property
    def configured(self) -> bool:
        return bool(self.config.enabled and self.config.endpoint and self.config.model)

    def status(self) -> dict[str, object]:
        return {
            "schema": "bingomate-local-llm-status/v1",
            "enabled": self.config.enabled,
            "configured": self.configured,
            "provider": self.config.provider,
            "endpoint": self.config.endpoint or "not configured",
            "model": self.config.model or "not configured",
            "timeout_seconds": self.config.timeout_seconds,
            "max_tokens": self.config.max_tokens,
            "dependency": "stdlib-urllib",
        }

    def respond(self, prompt: str, memories: list[str], identity_frame: str = "") -> dict[str, object] | None:
        if not self.configured:
            return None
        messages = self._messages(prompt, memories, identity_frame)
        if self.config.provider == "ollama":
            return self._respond_ollama(messages)
        return self._respond_openai_compatible(messages)

    def _respond_openai_compatible(self, messages: list[dict[str, str]]) -> dict[str, object] | None:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "stream": False,
            "temperature": 0.3,
        }
        data = self._post_json(_openai_compatible_url(self.config.endpoint), payload)
        if data is None:
            return None
        choices = data.get("choices") if isinstance(data, dict) else None
        if not choices:
            return None
        first = choices[0]
        if not isinstance(first, dict):
            return None
        message = first.get("message")
        content = message.get("content") if isinstance(message, dict) else first.get("text")
        if not content:
            return None
        return {
            "mode": "local-llm-openai-compatible",
            "response": str(content),
            "requires_cloud": False,
            "model": self.config.model,
            "provider": self.config.provider,
        }

    def _respond_ollama(self, messages: list[dict[str, str]]) -> dict[str, object] | None:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": self.config.max_tokens,
                "temperature": 0.3,
            },
        }
        data = self._post_json(_ollama_chat_url(self.config.endpoint), payload)
        if not isinstance(data, dict):
            return None
        message = data.get("message")
        content = message.get("content") if isinstance(message, dict) else data.get("response")
        if not content:
            return None
        return {
            "mode": "local-llm-ollama",
            "response": str(content),
            "requires_cloud": False,
            "model": self.config.model,
            "provider": self.config.provider,
        }

    def _post_json(self, url: str, payload: dict[str, object]) -> dict[str, object] | None:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except (TimeoutError, OSError, urllib.error.URLError, urllib.error.HTTPError):
            return None
        try:
            decoded = json.loads(body)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, dict) else None

    def _messages(self, prompt: str, memories: list[str], identity_frame: str) -> list[dict[str, str]]:
        memory_context = "\n".join(f"- {memory}" for memory in memories[:5])
        system = (
            "You are Bingo, a privacy-first Jetson AI companion. Be concise, practical, "
            "permission-aware, and clear when an action is simulated, local, blocked, or needs approval."
        )
        if identity_frame:
            system = f"{system}\n\nIdentity frame:\n{identity_frame}"
        user = prompt if not memory_context else f"Relevant local memories:\n{memory_context}\n\nUser request:\n{prompt}"
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]


def _openai_compatible_url(endpoint: str) -> str:
    cleaned = endpoint.rstrip("/")
    if cleaned.endswith("/v1/chat/completions") or cleaned.endswith("/chat/completions"):
        return cleaned
    if cleaned.endswith("/v1"):
        return f"{cleaned}/chat/completions"
    return f"{cleaned}/v1/chat/completions"


def _ollama_chat_url(endpoint: str) -> str:
    cleaned = endpoint.rstrip("/")
    if cleaned.endswith("/api/chat"):
        return cleaned
    return f"{cleaned}/api/chat"
