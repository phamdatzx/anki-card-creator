"""Pure pre-create checks shared by the Anki dialog and the Word Inbox server.

Each function returns the problems found; an empty list means the payload can
be written. The first entry is the headline, any further entries are bullets.
"""

from __future__ import annotations

from typing import Any

from .lookups.contracts import (
    GAP_MARK,
    CollocationItem,
    DefinitionResult,
    PhraseSense,
    VietnameseResult,
    WordFormPayload,
    WordPatternPayload,
)


def definition_problems(selected: list[DefinitionResult]) -> list[str]:
    return [] if selected else ["Select at least one definition."]


def _form_incomplete(item: Any) -> bool:
    return (
        not str(item.get("definition") or "").strip()
        or not str(item.get("vietnamese") or "").strip()
        or not item.get("examples")
    )


def word_form_problems(payload: WordFormPayload) -> list[str]:
    root = payload.get("rootWord") or {}
    others = payload.get("other") or []
    if not str(root.get("word") or "").strip() or not others:
        return ["Root word and one related form are required."]
    missing = ["root word"] if _form_incomplete(root) else []
    missing.extend(
        f'{item.get("word") or ""} ({item.get("type") or ""})'
        for item in others
        if _form_incomplete(item)
    )
    if not missing:
        return []
    return [
        "Each word form needs Vietnamese meaning, a definition, "
        "and at least one example:",
        *missing,
    ]


def word_pattern_problems(payload: WordPatternPayload) -> list[str]:
    if not str(payload.get("gap") or "").strip() or not str(
        payload.get("answer") or ""
    ).strip():
        return ["Gap and answer are required."]
    return []


def vietnamese_problems(selected: list[VietnameseResult]) -> list[str]:
    if not selected:
        return ["Select at least one English word."]
    missing = [
        f"result {index + 1}"
        for index, result in enumerate(selected)
        if not str(result.get("word") or "").strip()
    ]
    return ["Each selected result needs a word:", *missing] if missing else []


def sentence_problems(vietnamese: str, sentence: str) -> list[str]:
    if not vietnamese.strip() or not sentence.strip():
        return ["Vietnamese meaning and English sentence are required."]
    return []


def collocation_problems(selected: list[CollocationItem]) -> list[str]:
    if not selected:
        return ["Select at least one collocation."]
    missing = [
        str(item.get("collocation") or f"item {index + 1}")
        for index, item in enumerate(selected)
        if not str(item.get("answer") or "").strip()
        or str(item.get("gap") or "").count(GAP_MARK) != 1
    ]
    if not missing:
        return []
    return [
        f"Each collocation needs an answer and a gap sentence with exactly "
        f"one {GAP_MARK}:",
        *missing,
    ]


def phrase_problems(phrase: str, selected: list[PhraseSense]) -> list[str]:
    if not phrase.strip():
        return ["Enter the phrase."]
    if not selected:
        return ["Select at least one meaning."]
    missing = [
        f"meaning {index + 1}"
        for index, sense in enumerate(selected)
        if not str(sense.get("definition") or "").strip()
    ]
    return ["Each selected meaning needs a definition:", *missing] if missing else []


def problems_message(problems: list[str]) -> str:
    head, *bullets = problems
    return "\n".join([head, *(f"• {label}" for label in bullets)])
