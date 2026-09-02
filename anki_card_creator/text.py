from __future__ import annotations

from typing import Any


def as_text(values: Any, *, multiline: bool = False) -> str:
    if not values:
        return ""
    if isinstance(values, str):
        return values
    separator = "\n" if multiline else ", "
    return separator.join(str(value) for value in values if value)


def split_list(text: str, *, multiline: bool = False) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    parts = (
        cleaned.splitlines()
        if multiline and "\n" in cleaned
        else cleaned.split(",")
    )
    return [part.strip() for part in parts if part.strip()]


def parse_score(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def score_field_text(value: Any) -> str:
    parsed = parse_score(value)
    return "" if parsed is None else str(parsed)
