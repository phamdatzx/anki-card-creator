from __future__ import annotations

from typing import Any, TypedDict, cast


class DefinitionResult(TypedDict):
    definition: str
    vietnamese: str
    partOfSpeech: str
    ipa: str
    synonyms: list[str]
    examples: list[str]
    popularity: int | None
    difficulty: int | None


class NormalPayload(TypedDict):
    word: str
    results: list[DefinitionResult]


class RootWord(TypedDict):
    word: str
    type: str
    definition: str
    vietnamese: str
    examples: list[str]
    ipa: str
    popularity: int | None
    difficulty: int | None


class WordFormItem(TypedDict):
    word: str
    type: str
    definition: str
    vietnamese: str
    examples: list[str]
    ipa: str
    popularity: int | None
    difficulty: int | None


class WordFormPayload(TypedDict):
    rootWord: RootWord
    other: list[WordFormItem]


class WordPatternPayload(TypedDict):
    gap: str
    vietnamese: str
    answer: str
    pattern: str
    explanation: str
    examples: list[str]


class SentencePayload(TypedDict):
    vietnamese: str


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    return value


def _string(value: Any, path: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string")


def _string_list(value: Any, path: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise ValueError(f"{path} must be a list of strings")


def _nonempty_string(value: Any, path: str) -> None:
    _string(value, path)
    if not value.strip():
        raise ValueError(f"{path} must not be empty")


def _nonempty_string_list(value: Any, path: str) -> None:
    _string_list(value, path)
    if not value or any(not item.strip() for item in value):
        raise ValueError(f"{path} must contain at least one non-empty string")


def _score(value: Any, path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
        raise ValueError(f"{path} must be an integer from 1 to 5")


def _require(data: dict[str, Any], keys: tuple[str, ...], path: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValueError(f"{path} is missing: {', '.join(missing)}")


def validate_normal_payload(value: Any) -> NormalPayload:
    payload = _mapping(value, "response")
    _require(payload, ("word", "results"), "response")
    _string(payload["word"], "response.word")
    if not isinstance(payload["results"], list):
        raise ValueError("response.results must be a list")
    required = (
        "definition",
        "vietnamese",
        "partOfSpeech",
        "ipa",
        "synonyms",
        "examples",
        "popularity",
        "difficulty",
    )
    for index, raw in enumerate(payload["results"]):
        path = f"response.results[{index}]"
        item = _mapping(raw, path)
        _require(item, required, path)
        for key in ("definition", "vietnamese", "partOfSpeech", "ipa"):
            _string(item[key], f"{path}.{key}")
        for key in ("synonyms", "examples"):
            _string_list(item[key], f"{path}.{key}")
        for key in ("popularity", "difficulty"):
            _score(item[key], f"{path}.{key}")
    return cast(NormalPayload, payload)


def validate_word_form_payload(value: Any) -> WordFormPayload:
    payload = _mapping(value, "response")
    _require(payload, ("rootWord", "other"), "response")
    root = _mapping(payload["rootWord"], "response.rootWord")
    root_required = (
        "word",
        "type",
        "definition",
        "vietnamese",
        "examples",
        "ipa",
        "popularity",
        "difficulty",
    )
    _require(root, root_required, "response.rootWord")
    for key in ("word", "type", "ipa"):
        _string(root[key], f"response.rootWord.{key}")
    _nonempty_string(root["definition"], "response.rootWord.definition")
    _nonempty_string(root["vietnamese"], "response.rootWord.vietnamese")
    _nonempty_string_list(root["examples"], "response.rootWord.examples")
    for key in ("popularity", "difficulty"):
        _score(root[key], f"response.rootWord.{key}")
    if not isinstance(payload["other"], list):
        raise ValueError("response.other must be a list")
    item_required = (
        "word",
        "type",
        "definition",
        "vietnamese",
        "examples",
        "ipa",
        "popularity",
        "difficulty",
    )
    for index, raw in enumerate(payload["other"]):
        path = f"response.other[{index}]"
        item = _mapping(raw, path)
        _require(item, item_required, path)
        for key in ("word", "type", "ipa"):
            _string(item[key], f"{path}.{key}")
        _nonempty_string(item["definition"], f"{path}.definition")
        _nonempty_string(item["vietnamese"], f"{path}.vietnamese")
        _nonempty_string_list(item["examples"], f"{path}.examples")
        for key in ("popularity", "difficulty"):
            _score(item[key], f"{path}.{key}")
    return cast(WordFormPayload, payload)


def validate_word_pattern_payload(value: Any) -> WordPatternPayload:
    payload = _mapping(value, "response")
    required = (
        "gap",
        "vietnamese",
        "answer",
        "pattern",
        "explanation",
        "examples",
    )
    _require(payload, required, "response")
    for key in ("gap", "vietnamese", "answer", "pattern", "explanation"):
        _string(payload[key], f"response.{key}")
    _string_list(payload["examples"], "response.examples")
    return cast(WordPatternPayload, payload)


def validate_sentence_payload(value: Any) -> SentencePayload:
    payload = _mapping(value, "response")
    _require(payload, ("vietnamese",), "response")
    _string(payload["vietnamese"], "response.vietnamese")
    return cast(SentencePayload, payload)
