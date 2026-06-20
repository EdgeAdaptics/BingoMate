from __future__ import annotations

from bingomate.reasoning.local_adapter import LocalLLMAdapter, LocalLLMConfig
from bingomate.reasoning.openai_adapter import OpenAIReasoningAdapter


class ReasoningEngine:
    def __init__(
        self,
        cloud_assist: bool = False,
        openai_model: str = "",
        local_llm_enabled: bool = False,
        local_llm_url: str = "",
        local_llm_model: str = "",
        local_llm_provider: str = "openai-compatible",
        local_llm_timeout_seconds: float = 20.0,
        local_llm_max_tokens: int = 512,
    ) -> None:
        self.cloud_assist = cloud_assist
        self.openai_model = openai_model
        self.local_llm = LocalLLMAdapter(
            LocalLLMConfig(
                enabled=local_llm_enabled,
                provider=local_llm_provider,
                endpoint=local_llm_url,
                model=local_llm_model,
                timeout_seconds=local_llm_timeout_seconds,
                max_tokens=local_llm_max_tokens,
            )
        )

    def status(self) -> dict[str, object]:
        local_status = self.local_llm.status()
        default_mode = "local-simulation"
        if self.local_llm.configured:
            default_mode = f"local-llm-{self.local_llm.config.provider}"
        elif self.cloud_assist and self.openai_model:
            default_mode = "openai-responses-api"
        return {
            "schema": "bingomate-reasoning-status/v1",
            "default_mode": default_mode,
            "active_order": ["local_llm", "cloud_assist", "deterministic_fallback"],
            "local_llm": local_status,
            "cloud_assist": {
                "enabled": self.cloud_assist,
                "configured": bool(self.cloud_assist and self.openai_model),
                "model": self.openai_model or "not configured",
            },
            "deterministic_fallback": {
                "enabled": True,
                "mode": "local-simulation",
            },
        }

    def respond(
        self,
        prompt: str,
        memories: list[str] | None = None,
        identity_frame: str = "",
    ) -> dict[str, object]:
        local_response = self.local_llm.respond(prompt, memories or [], identity_frame)
        if local_response is not None:
            return local_response

        if self.cloud_assist:
            cloud_response = OpenAIReasoningAdapter(self.openai_model).respond(prompt, memories or [])
            if cloud_response is not None:
                return cloud_response

        memory_note = f" I found {len(memories)} relevant memories." if memories else ""
        identity_note = f" {identity_frame}" if identity_frame else ""
        return {
            "mode": "local-simulation",
            "response": (
                f"I am Bingo. I can help with: {_sentence(prompt)}{memory_note}{identity_note} "
                "I will keep private context local unless you explicitly enable a cloud path."
            ),
            "requires_cloud": False,
            "fallbacks": {
                "local_llm_configured": self.local_llm.configured,
                "cloud_assist_requested": self.cloud_assist,
            },
        }


def _sentence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return "your request."
    if cleaned[-1] in ".!?":
        return cleaned
    return f"{cleaned}."
