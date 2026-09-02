from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any


class OpenAIError(Exception):
    """Raised when an OpenAI-compatible request fails."""


def ssl_context(verify_ssl: bool) -> ssl.SSLContext:
    if not verify_ssl:
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def error_detail(raw: str, fallback: object) -> str:
    detail = raw or str(fallback)
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return detail
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        message = payload["error"].get("message")
        if message:
            return str(message)
    return detail


def _post(
    url: str,
    body: dict[str, Any],
    *,
    api_key: str,
    verify_ssl: bool,
    timeout: int,
    accept: str,
    operation: str,
) -> bytes:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Accept": accept,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Anki Card Creator",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=timeout, context=ssl_context(verify_ssl)
        ) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise OpenAIError(
            f"OpenAI {operation} error {exc.code}: {error_detail(raw, exc.reason)}"
        ) from exc
    except urllib.error.URLError as exc:
        raise OpenAIError(f"Network error: {exc.reason}") from exc


def speech_mp3(
    *,
    api_key: str,
    text: str,
    base_url: str,
    model: str = "gpt-4o-mini-tts",
    voice: str = "alloy",
    instructions: str = "",
    verify_ssl: bool = False,
    timeout: int = 60,
) -> bytes:
    cleaned = text.strip()
    if not api_key:
        raise OpenAIError(
            "Missing OpenAI key. Set openai_api_key in Tools → Add-ons → "
            "Anki Card Creator → Config."
        )
    if not cleaned:
        raise OpenAIError("Cannot generate audio for an empty word.")
    if not model:
        raise OpenAIError("Missing openai_tts_model in add-on config.")
    if not voice:
        raise OpenAIError("Missing openai_tts_voice in add-on config.")
    body = {
        "model": model,
        "voice": voice,
        "input": cleaned,
        "response_format": "mp3",
    }
    if instructions.strip():
        body["instructions"] = instructions.strip()
    audio = _post(
        f"{(base_url or 'https://api.openai.com/v1').rstrip('/')}/audio/speech",
        body,
        api_key=api_key,
        verify_ssl=verify_ssl,
        timeout=timeout,
        accept="audio/mpeg",
        operation="TTS",
    )
    if not audio:
        raise OpenAIError("OpenAI TTS returned empty audio.")
    return audio


def parse_chat_response(raw: bytes | str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise OpenAIError("OpenAI returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise OpenAIError("Unexpected OpenAI response.")
    choices = payload.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        raise OpenAIError("OpenAI returned no choices.")
    message = choices[0].get("message") or {}
    if not isinstance(message, dict):
        raise OpenAIError("Unexpected OpenAI response.")
    if message.get("refusal"):
        raise OpenAIError(f"Model refused: {message['refusal']}")
    content = message.get("content")
    if not content:
        raise OpenAIError("OpenAI returned empty content.")
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise OpenAIError("Model returned non-JSON content.") from exc
    if not isinstance(data, dict):
        raise OpenAIError("Unexpected structured output.")
    return data


def chat_json(
    *,
    api_key: str,
    model: str,
    base_url: str,
    system: str,
    user: str,
    schema_name: str,
    schema: dict[str, Any],
    verify_ssl: bool = False,
    timeout: int = 60,
) -> dict[str, Any]:
    if not api_key:
        raise OpenAIError(
            "Missing OpenAI key. Set openai_api_key in Tools → Add-ons → "
            "Anki Card Creator → Config."
        )
    if not model:
        raise OpenAIError("Missing openai_model in add-on config.")
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
    }
    raw = _post(
        f"{(base_url or 'https://api.openai.com/v1').rstrip('/')}/chat/completions",
        body,
        api_key=api_key,
        verify_ssl=verify_ssl,
        timeout=timeout,
        accept="application/json",
        operation="chat",
    )
    return parse_chat_response(raw)
