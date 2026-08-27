from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .api import ssl_context


class LlmError(Exception):
    """Raised when an OpenAI request fails."""


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
        raise LlmError(
            "Missing OpenAI key. Set openai_api_key in Tools → Add-ons → VIP Translate → Config."
        )
    if not model:
        raise LlmError("Missing openai_model in add-on config.")

    base = (base_url or "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/chat/completions"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=timeout, context=ssl_context(verify_ssl)
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        detail = raw or exc.reason
        try:
            err = json.loads(raw)
            if isinstance(err, dict) and isinstance(err.get("error"), dict):
                detail = err["error"].get("message") or detail
        except json.JSONDecodeError:
            pass
        raise LlmError(f"OpenAI error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LlmError(f"Network error: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise LlmError("OpenAI returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise LlmError("Unexpected OpenAI response.")

    choices = payload.get("choices") or []
    if not choices:
        raise LlmError("OpenAI returned no choices.")

    message = choices[0].get("message") or {}
    refusal = message.get("refusal")
    if refusal:
        raise LlmError(f"Model refused: {refusal}")

    content = message.get("content")
    if not content:
        raise LlmError("OpenAI returned empty content.")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LlmError("Model returned non-JSON content.") from exc

    if not isinstance(data, dict):
        raise LlmError("Unexpected structured output.")
    return data
