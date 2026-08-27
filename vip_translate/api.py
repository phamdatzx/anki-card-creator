from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class WordsApiError(Exception):
    """Raised when the WordsAPI request fails."""


def ssl_context(verify_ssl: bool) -> ssl.SSLContext:
    # Anki's bundled OpenSSL often fails CA checks (e.g. Missing Authority Key
    # Identifier) even when the same URL works in Postman/browsers.
    if not verify_ssl:
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def fetch_word(
    word: str,
    api_key: str,
    host: str,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    cleaned = word.strip()
    if not cleaned:
        raise WordsApiError("Enter a word to look up.")
    if not api_key:
        raise WordsApiError(
            "Missing RapidAPI key. Set rapidapi_key in Tools → Add-ons → VIP Translate → Config."
        )

    encoded = urllib.parse.quote(cleaned)
    url = f"https://{host}/words/{encoded}"
    # Cloudflare error 1010 bans default Python-urllib User-Agent; mirror a browser.
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "x-rapidapi-host": host,
            "x-rapidapi-key": api_key,
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=20, context=ssl_context(verify_ssl)
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise WordsApiError(f'No results for "{cleaned}".') from exc
        body = exc.read().decode("utf-8", errors="replace")
        raise WordsApiError(f"API error {exc.code}: {body or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise WordsApiError(f"Network error: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise WordsApiError("API returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise WordsApiError("Unexpected API response.")
    return payload
