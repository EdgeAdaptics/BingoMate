from __future__ import annotations

import json
import io
import math
import os
import shutil
import shlex
import subprocess
import struct
import tempfile
import time
import urllib.error
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VoiceSynthesis:
    wav: bytes
    mode: str
    text: str
    sample_rate: int


@dataclass(frozen=True)
class LocalSTTConfig:
    enabled: bool = False
    provider: str = "openai-compatible"
    endpoint: str = ""
    model: str = ""
    command: str = ""
    timeout_seconds: float = 30.0


class VoicePipeline:
    def __init__(
        self,
        wake_word: str = "hey bingo",
        stt_enabled: bool = False,
        stt_provider: str = "openai-compatible",
        stt_url: str = "",
        stt_model: str = "",
        stt_command: str = "",
        stt_timeout_seconds: float = 30.0,
    ) -> None:
        self.wake_word = wake_word
        provider = stt_provider.strip().lower()
        if provider not in {"openai-compatible", "command"}:
            provider = "openai-compatible"
        self.stt = LocalSTTConfig(
            enabled=stt_enabled,
            provider=provider,
            endpoint=stt_url.strip(),
            model=stt_model.strip(),
            command=stt_command.strip(),
            timeout_seconds=min(max(float(stt_timeout_seconds), 1.0), 300.0),
        )

    @property
    def stt_configured(self) -> bool:
        if not self.stt.enabled:
            return False
        if self.stt.provider == "command":
            return bool(self.stt.command)
        return bool(self.stt.endpoint and self.stt.model)

    def stt_status(self) -> dict[str, object]:
        command_name = first_command_token(self.stt.command)
        return {
            "schema": "bingomate-stt-status/v1",
            "wake_word": self.wake_word,
            "enabled": self.stt.enabled,
            "configured": self.stt_configured,
            "provider": self.stt.provider,
            "endpoint": self.stt.endpoint or "not configured",
            "model": self.stt.model or "not configured",
            "command_configured": bool(self.stt.command),
            "command_available": bool(command_name and shutil.which(command_name)),
            "timeout_seconds": self.stt.timeout_seconds,
            "simulation_fallback": True,
            "privacy": "audio is processed locally and is not stored by the STT endpoint",
        }

    def simulate_transcript(self, audio_hint: str) -> dict[str, object]:
        text = sanitize_voice_text(audio_hint)
        wake_detected = text.lower().startswith(self.wake_word)
        return {
            "wake_detected": wake_detected,
            "wake_word_detected": wake_detected,
            "text": text,
            "mode": "local-simulation",
            "prompt": self.prompt_from_transcript(text) if wake_detected else "",
        }

    def transcribe_audio_bytes(
        self,
        audio: bytes,
        content_type: str = "audio/wav",
        audio_hint: str = "",
    ) -> dict[str, object]:
        if not audio:
            simulated = self.simulate_transcript(audio_hint)
            return {
                **simulated,
                "schema": "bingomate-stt-transcript/v1",
                "accepted": bool(audio_hint),
                "reason": "audio_missing_simulation_hint_used" if audio_hint else "audio_missing",
                "stt_status": self.stt_status(),
            }
        transcript = ""
        mode = ""
        reason = ""
        if self.stt_configured and self.stt.provider == "command":
            transcript, reason = self._transcribe_with_command(audio, content_type)
            mode = "local-stt-command"
        elif self.stt_configured:
            transcript, reason = self._transcribe_with_openai_compatible(audio, content_type)
            mode = "local-stt-openai-compatible"
        else:
            reason = "stt_not_configured"
        if not transcript:
            simulated = self.simulate_transcript(audio_hint)
            return {
                **simulated,
                "schema": "bingomate-stt-transcript/v1",
                "accepted": bool(audio_hint),
                "reason": f"{reason}_simulation_hint_used" if audio_hint else reason,
                "stt_status": self.stt_status(),
            }
        transcript_result = self.simulate_transcript(transcript)
        return {
            **transcript_result,
            "schema": "bingomate-stt-transcript/v1",
            "accepted": True,
            "mode": mode,
            "reason": "transcribed",
            "stt_status": self.stt_status(),
        }

    def prompt_from_transcript(self, transcript: str) -> str:
        text = sanitize_voice_text(transcript)
        if text.lower().startswith(self.wake_word):
            text = text[len(self.wake_word) :].lstrip(" ,.:;-")
        return text or "status"

    def startup_phrase(self, assistant_name: str = "Bingo") -> str:
        return (
            f"{assistant_name} online. Local systems are waking up. "
            "I am running on the edge and keeping your context private."
        )

    def startup_chime_wav(self, sample_rate: int = 22050) -> bytes:
        notes = [
            (523.25, 0.10),
            (659.25, 0.12),
            (783.99, 0.10),
            (659.25, 0.08),
            (880.00, 0.14),
        ]
        samples: list[int] = []
        for frequency, duration in notes:
            frame_count = int(sample_rate * duration)
            for index in range(frame_count):
                progress = index / max(1, frame_count - 1)
                vibrato = 1.0 + 0.08 * math.sin(2 * math.pi * 6 * index / sample_rate)
                envelope = math.sin(math.pi * progress)
                value = 0.35 * envelope * vibrato * math.sin(2 * math.pi * frequency * index / sample_rate)
                samples.append(int(max(-1.0, min(1.0, value)) * 32767))
            pause = [0] * int(sample_rate * 0.05)
            samples.extend(pause)
        return wav_from_samples(samples, sample_rate)

    def synthesize_speech(self, text: str, sample_rate: int = 22050) -> VoiceSynthesis:
        safe_text = sanitize_voice_text(text)
        external = synthesize_with_espeak(safe_text)
        if external:
            return VoiceSynthesis(wav=external, mode="local-espeak", text=safe_text, sample_rate=sample_rate)
        return VoiceSynthesis(
            wav=self._prosody_fallback_wav(safe_text, sample_rate),
            mode="local-prosody-fallback",
            text=safe_text,
            sample_rate=sample_rate,
        )

    def _prosody_fallback_wav(self, text: str, sample_rate: int) -> bytes:
        words = text.split()[:80] or ["Bingo", "ready"]
        samples: list[int] = []
        base_frequencies = [349.23, 392.0, 440.0, 523.25, 587.33, 659.25]
        for word_index, word in enumerate(words):
            word_value = sum(ord(character) for character in word)
            frequency = base_frequencies[word_value % len(base_frequencies)]
            duration = min(0.18, 0.045 + (len(word) * 0.012))
            frame_count = int(sample_rate * duration)
            for index in range(frame_count):
                progress = index / max(1, frame_count - 1)
                envelope = math.sin(math.pi * progress)
                modulation = 1.0 + 0.04 * math.sin(2 * math.pi * 5 * index / sample_rate)
                value = 0.26 * envelope * math.sin(2 * math.pi * frequency * modulation * index / sample_rate)
                samples.append(int(max(-1.0, min(1.0, value)) * 32767))
            gap = 0.026 if word.endswith((".", "?", "!")) else 0.014
            samples.extend([0] * int(sample_rate * gap))
            if word_index % 9 == 8:
                samples.extend([0] * int(sample_rate * 0.045))
        return wav_from_samples(samples, sample_rate)

    def _transcribe_with_command(self, audio: bytes, content_type: str) -> tuple[str, str]:
        suffix = suffix_for_content_type(content_type)
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / f"bingomate-stt{suffix}"
            audio_path.write_bytes(audio)
            command = self.stt.command.format(audio=str(audio_path), model=self.stt.model)
            args = shlex.split(command, posix=os.name != "nt")
            if not args:
                return "", "stt_command_missing"
            try:
                completed = subprocess.run(
                    args,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=self.stt.timeout_seconds,
                )
            except (OSError, subprocess.SubprocessError):
                return "", "stt_command_failed"
            if completed.returncode != 0:
                return "", "stt_command_nonzero_exit"
            if not completed.stdout.strip():
                return "", "stt_command_empty_transcript"
            return sanitize_voice_text(completed.stdout), "transcribed"

    def _transcribe_with_openai_compatible(self, audio: bytes, content_type: str) -> tuple[str, str]:
        boundary = f"bingomate{int(time.time() * 1000)}"
        body = multipart_audio_body(boundary, self.stt.model, audio, content_type)
        request = urllib.request.Request(
            openai_audio_transcription_url(self.stt.endpoint),
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.stt.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, OSError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            return "", "stt_endpoint_failed"
        if not isinstance(payload, dict):
            return "", "stt_endpoint_invalid_response"
        text = payload.get("text") or payload.get("transcript")
        if not text:
            return "", "stt_endpoint_empty_transcript"
        return sanitize_voice_text(str(text)), "transcribed"


def sanitize_voice_text(value: str, max_length: int = 600) -> str:
    text = " ".join(value.replace("\x00", " ").split())
    return text[:max_length] or "Bingo ready."


def suffix_for_content_type(content_type: str) -> str:
    lowered = content_type.lower()
    if "mpeg" in lowered or "mp3" in lowered:
        return ".mp3"
    if "webm" in lowered:
        return ".webm"
    if "ogg" in lowered:
        return ".ogg"
    return ".wav"


def first_command_token(command: str) -> str:
    if not command:
        return ""
    try:
        return shlex.split(command, posix=os.name != "nt")[0]
    except (IndexError, ValueError):
        return ""


def openai_audio_transcription_url(endpoint: str) -> str:
    cleaned = endpoint.rstrip("/")
    if cleaned.endswith("/v1/audio/transcriptions") or cleaned.endswith("/audio/transcriptions"):
        return cleaned
    if cleaned.endswith("/v1"):
        return f"{cleaned}/audio/transcriptions"
    return f"{cleaned}/v1/audio/transcriptions"


def multipart_audio_body(boundary: str, model: str, audio: bytes, content_type: str) -> bytes:
    lines = [
        f"--{boundary}",
        'Content-Disposition: form-data; name="model"',
        "",
        model,
        f"--{boundary}",
        'Content-Disposition: form-data; name="file"; filename="bingomate-audio.wav"',
        f"Content-Type: {content_type or 'audio/wav'}",
        "",
    ]
    head = "\r\n".join(lines).encode("utf-8") + b"\r\n"
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return head + audio + tail


def synthesize_with_espeak(text: str) -> bytes | None:
    executable = shutil.which("espeak-ng") or shutil.which("espeak")
    if not executable:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        output_path = Path(tmp) / "bingomate-voice.wav"
        try:
            subprocess.run(
                [executable, "-w", str(output_path), "--stdin"],
                input=text,
                text=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
            )
            return output_path.read_bytes()
        except (OSError, subprocess.SubprocessError):
            return None


def wav_from_samples(samples: list[int], sample_rate: int) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))
    return output.getvalue()
