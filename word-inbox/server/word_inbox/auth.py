from __future__ import annotations

import hashlib
import hmac
import time


def check_password(given: str, expected: str) -> bool:
    return bool(expected) and hmac.compare_digest(
        given.encode("utf-8"), expected.encode("utf-8")
    )


def _signature(secret: str, expires: int) -> str:
    return hmac.new(
        secret.encode("utf-8"), str(expires).encode("ascii"), hashlib.sha256
    ).hexdigest()


def issue_token(secret: str, ttl_seconds: int, now: float | None = None) -> str:
    expires = int((time.time() if now is None else now) + ttl_seconds)
    return f"{expires}.{_signature(secret, expires)}"


def verify_token(secret: str, token: str, now: float | None = None) -> bool:
    expires_text, _, signature = token.partition(".")
    if not expires_text.isdigit() or not signature:
        return False
    expires = int(expires_text)
    if expires < (time.time() if now is None else now):
        return False
    return hmac.compare_digest(signature, _signature(secret, expires))
