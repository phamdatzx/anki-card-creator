from __future__ import annotations

from typing import Any

from .llm import LlmError, chat_json

_STRING_LIST = {
    "type": "array",
    "items": {"type": "string"},
}

PHRASAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "word": {"type": "string"},
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "definition": {"type": "string"},
                    "partOfSpeech": {"type": "string"},
                    "synonyms": _STRING_LIST,
                    "examples": _STRING_LIST,
                },
                "required": [
                    "definition",
                    "partOfSpeech",
                    "synonyms",
                    "examples",
                ],
            },
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
            },
            "required": ["word", "type", "definition"],
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
                },
                "required": ["word", "type", "special_definition"],
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
        "answer": {"type": "string"},
        "pattern": {"type": "string"},
        "explanation": {"type": "string"},
        "examples": _STRING_LIST,
    },
    "required": ["gap", "answer", "pattern", "explanation", "examples"],
}

# Same shape as WordsAPI-style definition lists (Normal + Phrasal).
NORMAL_SCHEMA = PHRASAL_SCHEMA

_NORMAL_SYSTEM = """You are an English vocabulary learning assistant.
Given a single English word, return distinct dictionary-style senses for learners.
Use clear short definitions, natural examples, and relevant synonyms.
partOfSpeech should be a short label (noun, verb, adjective, adverb, etc.).
Return only data that matches the schema."""

_PHRASAL_SYSTEM = """You are an English vocabulary learning assistant.
Given a phrasal verb, return distinct senses suitable for learners.
Use clear short definitions, British/American-neutral examples, and relevant synonyms.
partOfSpeech should usually be "phrasal verb" unless another label is clearly better.
Return only data that matches the schema."""

_WORD_FORM_SYSTEM = """You are an English vocabulary learning assistant.
Given a root word, return its word family: the root plus related forms
(noun/verb/adjective/adverb/etc.).
Use special_definition for meaning of the related form;
Keep type labels short (e.g. noun, verb, adjective, adverb).
Return only data that matches the schema."""

_WORD_PATTERN_SYSTEM = """You are an English question creator for learning.
Given a collocation or usage pattern (e.g. "make a decision", "on purpose"),
create one gap-fill question.
gap must hide the key lexical item with "__"
gap can hide all the word or some part: (She __ a decision to quit her job)
the question should be long enough to provide context(1-2 sentences). Make sure the user can guess the answer.
answer is the missing text; pattern is the full pattern; explanation briefly
describes the usage; examples are natural sentences.
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
        raise LlmError("Enter a word to look up.")
    return _call(
        api_key=api_key,
        model=model,
        base_url=base_url,
        verify_ssl=verify_ssl,
        system=_NORMAL_SYSTEM,
        user=f"Word: {cleaned}",
        schema_name="normal_word_lookup",
        schema=NORMAL_SCHEMA,
    )


def lookup_phrasal_verb(
    phrase: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    cleaned = phrase.strip()
    if not cleaned:
        raise LlmError("Enter a phrasal verb to look up.")
    return _call(
        api_key=api_key,
        model=model,
        base_url=base_url,
        verify_ssl=verify_ssl,
        system=_PHRASAL_SYSTEM,
        user=f"Phrasal verb: {cleaned}",
        schema_name="phrasal_verb_lookup",
        schema=PHRASAL_SCHEMA,
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
        raise LlmError("Enter a root word to look up.")
    return _call(
        api_key=api_key,
        model=model,
        base_url=base_url,
        verify_ssl=verify_ssl,
        system=_WORD_FORM_SYSTEM,
        user=f"Root word: {cleaned}",
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
