from __future__ import annotations

from typing import Any

from .llm import LlmError, chat_json

_STRING_LIST = {
    "type": "array",
    "items": {"type": "string"},
}

_SCORE_1_TO_5 = {
    "type": "integer",
}

_DEFINITION_RESULT = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "definition": {"type": "string"},
        "vietnamese": {"type": "string"},
        "partOfSpeech": {"type": "string"},
        "ipa": {"type": "string"},
        "synonyms": _STRING_LIST,
        "examples": _STRING_LIST,
        "popularity": _SCORE_1_TO_5,
        "difficulty": _SCORE_1_TO_5,
    },
    "required": [
        "definition",
        "vietnamese",
        "partOfSpeech",
        "ipa",
        "synonyms",
        "examples",
        "popularity",
        "difficulty",
    ],
}

NORMAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "word": {"type": "string"},
        "results": {
            "type": "array",
            "items": _DEFINITION_RESULT,
        },
    },
    "required": ["word", "results"],
}

WORD_FORM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "rootWord": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "word": {"type": "string"},
                "type": {"type": "string"},
                "definition": {"type": "string"},
                "vietnamese": {"type": "string"},
                "ipa": {"type": "string"},
                "popularity": _SCORE_1_TO_5,
                "difficulty": _SCORE_1_TO_5,
            },
            "required": [
                "word",
                "type",
                "definition",
                "vietnamese",
                "ipa",
                "popularity",
                "difficulty",
            ],
        },
        "other": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "word": {"type": "string"},
                    "type": {"type": "string"},
                    "special_definition": {"type": ["string", "null"]},
                    "ipa": {"type": "string"},
                    "popularity": _SCORE_1_TO_5,
                    "difficulty": _SCORE_1_TO_5,
                },
                "required": [
                    "word",
                    "type",
                    "special_definition",
                    "ipa",
                    "popularity",
                    "difficulty",
                ],
            },
        },
    },
    "required": ["rootWord", "other"],
}

WORD_PATTERN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "gap": {"type": "string"},
        "vietnamese": {"type": "string"},
        "answer": {"type": "string"},
        "pattern": {"type": "string"},
        "explanation": {"type": "string"},
        "examples": _STRING_LIST,
    },
    "required": [
        "gap",
        "vietnamese",
        "answer",
        "pattern",
        "explanation",
        "examples",
    ],
}

_SCORE_GUIDANCE = """For each sense / form, rate it for learners (not the whole word once):
- popularity: integer 1–5 (5 = that sense/form is very common in everyday English; 1 = rare / specialist)
- difficulty: integer 1–5 (5 = that sense/form is very hard for intermediate learners; 1 = easy / beginner-friendly)
Different senses of the same word can have different scores. Use your best judgment; be consistent."""

_NORMAL_SYSTEM = f"""You are an English vocabulary learning assistant.
Given an English word or phrasal verb, return distinct dictionary-style senses
for learners.
Use clear short definitions, Vietnamese meanings, natural examples, and relevant
synonyms.
partOfSpeech should be a short label (noun, verb, adjective, adverb, etc.).
For phrasal verbs, use "phrasal verb" unless another label is clearly better.
For every sense, provide its precise standard American English IPA in slash notation
(e.g. /ˈrɛkərd/), using the pronunciation appropriate to that sense.
{_SCORE_GUIDANCE}
Return only data that matches the schema."""

_WORD_FORM_SYSTEM = f"""You are an English vocabulary learning assistant.
The user may type ANY form from a word family (root, adverb, noun, etc.) — not always the root.
Identify the true morphological base / lemma as rootWord (e.g. input "neatly" → rootWord.word = "neat",
type adjective; include "neatly" in other as the adverb).
If the input is already the best root, use it as rootWord.
Return the word family: rootWord plus related forms in other
(noun/verb/adjective/adverb/etc.).
Do not treat a derived form as root just because it was typed.
Provide a short natural Vietnamese meaning for rootWord.
Use special_definition for meaning of the related form;
Keep type labels short (e.g. noun, verb, adjective, adverb).
Provide precise standard American English IPA in slash notation for rootWord and
each related form (e.g. /ˈniːtli/).
{_SCORE_GUIDANCE}
Rate popularity and difficulty on the rootWord and on each related form separately.
Return only data that matches the schema."""

_WORD_PATTERN_SYSTEM = """You are an English question creator for Vietnamese learners.
Given a collocation or usage pattern (e.g. "make a decision", "on purpose"),
create one gap-fill question in a natural English context (1–2 sentences).

Rules:
1. ALWAYS hide the ENTIRE target pattern — never leave any part of it visible.
2. In the gap sentence, put the Vietnamese meaning of that pattern where it was
   removed, inside parentheses. Example:
   pattern "make a decision" →
   gap: "After thinking carefully, she (đưa ra quyết định) to leave the company."
   answer: "made a decision" (or the exact English words that fill the blank,
   conjugated to fit the sentence)
3. vietnamese: short natural Vietnamese gloss of the pattern (same text as inside
   the parentheses in gap).
4. pattern: the full English collocation/pattern in base form.
5. explanation: brief English usage note; examples: natural English sentences.
Return only data that matches the schema."""


def _call(
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool,
    system: str,
    user: str,
    schema_name: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    return chat_json(
        api_key=api_key,
        model=model,
        base_url=base_url,
        system=system,
        user=user,
        schema_name=schema_name,
        schema=schema,
        verify_ssl=verify_ssl,
    )


def lookup_normal_word(
    word: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    cleaned = word.strip()
    if not cleaned:
        raise LlmError("Enter a word or phrasal verb to look up.")
    return _call(
        api_key=api_key,
        model=model,
        base_url=base_url,
        verify_ssl=verify_ssl,
        system=_NORMAL_SYSTEM,
        user=f"Vocabulary entry: {cleaned}",
        schema_name="vocabulary_entry_lookup",
        schema=NORMAL_SCHEMA,
    )


def lookup_word_form(
    word: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    cleaned = word.strip()
    if not cleaned:
        raise LlmError("Enter a word to look up (any form in the family).")
    return _call(
        api_key=api_key,
        model=model,
        base_url=base_url,
        verify_ssl=verify_ssl,
        system=_WORD_FORM_SYSTEM,
        user=f"Word (any form; find the true root): {cleaned}",
        schema_name="word_form_lookup",
        schema=WORD_FORM_SCHEMA,
    )


def lookup_word_pattern(
    pattern: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    cleaned = pattern.strip()
    if not cleaned:
        raise LlmError("Enter a word pattern / collocation.")
    return _call(
        api_key=api_key,
        model=model,
        base_url=base_url,
        verify_ssl=verify_ssl,
        system=_WORD_PATTERN_SYSTEM,
        user=f"Pattern: {cleaned}",
        schema_name="word_pattern_lookup",
        schema=WORD_PATTERN_SCHEMA,
    )
