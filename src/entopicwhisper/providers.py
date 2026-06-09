from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from .config import AppConfig
from .text import build_cleanup_prompt, build_meeting_summary_prompt, strip_empty_marker


class ProviderError(RuntimeError):
    pass


def _headers(config: AppConfig) -> dict[str, str]:
    key = config.api_key()
    if not key:
        raise ProviderError(
            f"Missing API key. Set {config.api_key_env}=... or edit "
            f"{config.config_dir / 'config.env'}"
        )
    return {"Authorization": f"Bearer {key}"}


def transcribe_audio(audio_path: Path, config: AppConfig) -> str:
    url = f"{config.api_base.rstrip('/')}/audio/transcriptions"
    with audio_path.open("rb") as audio:
        response = requests.post(
            url,
            headers=_headers(config),
            files={"file": (audio_path.name, audio, "audio/wav")},
            data={"model": config.model, "response_format": "json"},
            timeout=180,
        )
    if response.status_code >= 400:
        raise ProviderError(f"Transcription failed ({response.status_code}): {response.text[:500]}")
    data: dict[str, Any] = response.json()
    return str(data.get("text", "")).strip()


def chat_completion(prompt: str, config: AppConfig) -> str:
    url = f"{config.api_base.rstrip('/')}/chat/completions"
    response = requests.post(
        url,
        headers={**_headers(config), "Content-Type": "application/json"},
        data=json.dumps(
            {
                "model": config.llm_model,
                "messages": [
                    {"role": "system", "content": "You clean dictation and produce meeting notes."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            }
        ),
        timeout=180,
    )
    if response.status_code >= 400:
        raise ProviderError(f"Cleanup failed ({response.status_code}): {response.text[:500]}")
    data: dict[str, Any] = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise ProviderError("Cleanup returned no choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ProviderError("Cleanup returned empty content")
    return content.strip()


def cleanup_transcript(
    raw: str,
    config: AppConfig,
    *,
    context: str = "",
    mode: str = "dictation",
) -> str:
    prompt = build_cleanup_prompt(raw=raw, context=context, vocabulary=config.vocabulary, mode=mode)
    return strip_empty_marker(chat_completion(prompt, config))


def summarize_meeting(transcript: str, config: AppConfig) -> str:
    return chat_completion(build_meeting_summary_prompt(transcript, config.vocabulary), config)
