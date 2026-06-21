from __future__ import annotations

import os


class OpenAIReasoningAdapter:
    def __init__(self, model: str) -> None:
        self.model = model

    def respond(self, prompt: str, memories: list[str]) -> dict[str, object] | None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or not self.model:
            return None

        try:
            from openai import OpenAI
        except ImportError:
            return None

        client = OpenAI(api_key=api_key)
        memory_context = "\n".join(f"- {memory}" for memory in memories[:5])
        instructions = (
            "You are Bingo, a privacy-first Jetson AI companion. Be concise, practical, "
            "permission-aware, and clear when an action is simulated or needs approval."
        )
        user_input = prompt if not memory_context else f"Relevant local memories:\n{memory_context}\n\nUser request:\n{prompt}"
        response = client.responses.create(
            model=self.model,
            instructions=instructions,
            input=user_input,
        )
        return {
            "mode": "openai-responses-api",
            "response": response.output_text,
            "requires_cloud": True,
        }
