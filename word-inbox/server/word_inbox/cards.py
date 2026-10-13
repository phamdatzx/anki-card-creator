"""Lookup and card creation, mirroring the add-on dialog's flow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from anki_card_creator.audio import definition_audio_tags, word_form_audio
from anki_card_creator.config import AddonConfig, chat_kwargs
from anki_card_creator.create_checks import (
    definition_problems,
    sentence_problems,
    vietnamese_problems,
    word_form_problems,
    word_pattern_problems,
)
from anki_card_creator.lookups.contracts import (
    validate_normal_payload,
    validate_vietnamese_payload,
    validate_word_form_payload,
    validate_word_pattern_payload,
)
from anki_card_creator.lookups.normal import lookup_normal_word
from anki_card_creator.lookups.sentence import lookup_sentence
from anki_card_creator.lookups.vietnamese import lookup_vietnamese_word
from anki_card_creator.lookups.word_form import lookup_word_form
from anki_card_creator.lookups.word_pattern import lookup_word_pattern
from anki_card_creator.notes.normal import add_definition_notes
from anki_card_creator.notes.sentence import add_sentence_note
from anki_card_creator.notes.word_form import add_word_form_notes
from anki_card_creator.notes.word_pattern import add_word_pattern_note

_SCORES = ("popularity", "difficulty")
CARD_TYPES = ("normal", "word_form", "word_pattern", "sentence", "vietnamese")


class CardRequestError(ValueError):
    """The submitted payload cannot be written; ``problems`` explains why."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__(problems[0])
        self.problems = problems


def lookup(card_type: str, text: str, config: AddonConfig) -> dict[str, Any]:
    """Run the add-on lookup for ``card_type``; raises ``OpenAIError``."""
    kwargs = chat_kwargs(config)
    if card_type == "normal":
        return dict(lookup_normal_word(text, **kwargs))
    if card_type == "word_form":
        return dict(lookup_word_form(text, **kwargs))
    if card_type == "word_pattern":
        return dict(lookup_word_pattern(text, **kwargs))
    if card_type == "vietnamese":
        return dict(lookup_vietnamese_word(text, **kwargs))
    if card_type == "sentence":
        # The dialog pre-fills the English side with the looked-up sentence.
        return {**lookup_sentence(text, **kwargs), "sentence": text.strip()}
    raise CardRequestError([f"Unknown card type: {card_type}"])


def _scores_filled(value: Any) -> Any:
    """Copy for validation only: the editors may clear a score, as in Anki."""
    if isinstance(value, list):
        return [_scores_filled(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: 1 if key in _SCORES and item is None else _scores_filled(item)
        for key, item in value.items()
    }


def _validated(payload: Any, validate: Callable[[Any], Any]) -> None:
    try:
        validate(_scores_filled(payload))
    except ValueError as exc:
        raise CardRequestError([f"Invalid payload: {exc}"]) from exc


def _require_no_problems(problems: list[str]) -> None:
    if problems:
        raise CardRequestError(problems)


def _sentence(payload: dict[str, Any]) -> None:
    if not all(isinstance(payload.get(key), str) for key in ("vietnamese", "sentence")):
        raise ValueError("vietnamese and sentence must be strings")


def _dicts(values: Any) -> list[Any]:
    if not isinstance(values, list):
        return []
    return [item for item in values if isinstance(item, dict)]


def check_payload(card_type: str, payload: Any) -> Any:
    """Validate a payload the browser edited, like ``_create_cards`` does.

    Where the dialog's checks can run on a malformed payload they go first,
    because "Select at least one…" reads better than a schema error.
    """
    if not isinstance(payload, dict):
        raise CardRequestError(["Invalid payload: expected an object."])
    if card_type == "normal":
        _validated(payload, validate_normal_payload)
        _require_no_problems(definition_problems(payload["results"]))
    elif card_type == "vietnamese":
        _require_no_problems(vietnamese_problems(_dicts(payload.get("results"))))
        _validated(payload, validate_vietnamese_payload)
    elif card_type == "word_form":
        root = payload.get("rootWord")
        if isinstance(root, dict):
            _require_no_problems(
                word_form_problems(
                    {"rootWord": root, "other": _dicts(payload.get("other"))}  # type: ignore[typeddict-item]
                )
            )
        _validated(payload, validate_word_form_payload)
    elif card_type == "word_pattern":
        _validated(payload, validate_word_pattern_payload)
        _require_no_problems(word_pattern_problems(payload))  # type: ignore[arg-type]
    elif card_type == "sentence":
        _validated(payload, _sentence)
        payload = {key: payload[key].strip() for key in ("vietnamese", "sentence")}
        _require_no_problems(
            sentence_problems(payload["vietnamese"], payload["sentence"])
        )
    else:
        raise CardRequestError([f"Unknown card type: {card_type}"])
    return payload


def create_cards(
    col: Any,
    deck_id: int,
    card_type: str,
    payload: Any,
    config: AddonConfig,
    on_progress: Callable[[int, int], None] = lambda _current, _total: None,
) -> int:
    """Generate audio and add notes for a payload from ``check_payload``."""
    write_data = col.media.write_data
    if card_type == "normal":
        word = str(payload.get("word") or "")
        results = payload["results"]
        tags = definition_audio_tags(word, results, config, write_data, on_progress)
        return add_definition_notes(col, deck_id, word, "", "", tags, results)
    if card_type == "vietnamese":
        results = payload["results"]
        tags = definition_audio_tags("", results, config, write_data, on_progress)
        return add_definition_notes(col, deck_id, "", "", "", tags, results)
    if card_type == "word_form":
        root_audio, form_audio = word_form_audio(
            payload, config, write_data, on_progress
        )
        return add_word_form_notes(col, deck_id, payload, root_audio, form_audio)
    if card_type == "word_pattern":
        return add_word_pattern_note(col, deck_id, payload)
    if card_type == "sentence":
        return add_sentence_note(
            col, deck_id, payload["vietnamese"], payload["sentence"]
        )
    raise CardRequestError([f"Unknown card type: {card_type}"])
