from __future__ import annotations

from typing import Any

STRING_LIST: dict[str, Any] = {
    "type": "array",
    "items": {"type": "string"},
}
SCORE_1_TO_5: dict[str, Any] = {"type": "integer", "minimum": 1, "maximum": 5}

DEFINITION_RESULT: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "definition": {"type": "string"},
        "vietnamese": {"type": "string"},
        "partOfSpeech": {"type": "string"},
        "ipa": {"type": "string"},
        "synonyms": STRING_LIST,
        "examples": STRING_LIST,
        "popularity": SCORE_1_TO_5,
        "difficulty": SCORE_1_TO_5,
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
        "results": {"type": "array", "items": DEFINITION_RESULT},
    },
    "required": ["word", "results"],
}

ROOT_WORD: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "word": {"type": "string"},
        "type": {"type": "string"},
        "definition": {"type": "string"},
        "vietnamese": {"type": "string"},
        "ipa": {"type": "string"},
        "popularity": SCORE_1_TO_5,
        "difficulty": SCORE_1_TO_5,
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
}

WORD_FORM_ITEM: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "word": {"type": "string"},
        "type": {"type": "string"},
        "special_definition": {"type": ["string", "null"]},
        "ipa": {"type": "string"},
        "popularity": SCORE_1_TO_5,
        "difficulty": SCORE_1_TO_5,
    },
    "required": [
        "word",
        "type",
        "special_definition",
        "ipa",
        "popularity",
        "difficulty",
    ],
}

WORD_FORM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "rootWord": ROOT_WORD,
        "other": {"type": "array", "items": WORD_FORM_ITEM},
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
        "examples": STRING_LIST,
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

SENTENCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "vietnamese": {"type": "string"},
    },
    "required": ["vietnamese"],
}
