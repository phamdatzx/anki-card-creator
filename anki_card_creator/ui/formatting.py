from __future__ import annotations

from typing import Any

from ..text import parse_score


def scores_compact(data: dict[str, Any] | None) -> str:
    if not data:
        return ""
    popularity = parse_score(data.get("popularity"))
    difficulty = parse_score(data.get("difficulty"))
    parts = []
    if popularity is not None:
        parts.append(f"pop {popularity}/5")
    if difficulty is not None:
        parts.append(f"hard {difficulty}/5")
    return " · ".join(parts)


def item_label(result: dict[str, Any]) -> str:
    body = f"[{result.get('partOfSpeech') or '?'}] {result.get('definition') or ''}"
    ipa = str(result.get("ipa") or "").strip()
    if ipa:
        body += f"\n{ipa}"
    scores = scores_compact(result)
    return f"{scores}\n{body}" if scores else body


def vietnamese_item_label(result: dict[str, Any]) -> str:
    word = result.get("word") or "?"
    pos = result.get("partOfSpeech") or "?"
    body = f"{word} [{pos}] — {result.get('definition') or ''}"
    ipa = str(result.get("ipa") or "").strip()
    if ipa:
        body += f"\n{ipa}"
    scores = scores_compact(result)
    return f"{scores}\n{body}" if scores else body


def family_item_label(item: dict[str, Any]) -> str:
    word = item.get("word") or "?"
    pos = item.get("type") or "?"
    definition = item.get("definition") or ""
    vietnamese = item.get("vietnamese") or ""
    body = f"{word} ({pos}) — {vietnamese}\n{definition}"
    ipa = str(item.get("ipa") or "").strip()
    if ipa:
        body += f" {ipa}"
    scores = scores_compact(item)
    return f"{scores}\n{body}" if scores else body
