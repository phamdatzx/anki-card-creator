"""Lookup and card creation, mirroring the add-on dialog's flow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from anki_card_creator.audio import definition_audio_tags
from anki_card_creator.config import AddonConfig, chat_kwargs
from anki_card_creator.create_checks import (
    collocation_problems,
    normal_problems,
    phrase_problems,
    sentence_problems,
    vietnamese_problems,
    word_pattern_problems,
)
from anki_card_creator.lookups.collocation import lookup_collocations
from anki_card_creator.lookups.contracts import (
    validate_collocation_payload,
    validate_normal_payload,
    validate_phrase_payload,
    validate_vietnamese_payload,
    validate_word_pattern_payload,
)
from anki_card_creator.lookups.normal import lookup_normal_grouped
from anki_card_creator.lookups.phrase import lookup_phrase
from anki_card_creator.lookups.sentence import lookup_sentence
from anki_card_creator.lookups.vietnamese import lookup_vietnamese_word
from anki_card_creator.lookups.word_pattern import lookup_word_pattern
from anki_card_creator.notes.collocation import add_collocation_notes
from anki_card_creator.notes.normal import (
    add_definition_group_notes,
    add_definition_notes,
)
from anki_card_creator.notes.phrase import add_phrase_notes
from anki_card_creator.notes.sentence import add_sentence_note
from anki_card_creator.notes.word_pattern import add_word_pattern_note

_SCORES = ("popularity", "difficulty")
# Collocation and Phrase are Word Inbox only for now; the add-on dialog has
# no panel for them. Word form is add-on only: Word Inbox's Normal lookup
# finds the root word and offers its family as cards instead.
CARD_TYPES = (
    "normal",
    "word_pattern",
    "sentence",
    "vietnamese",
    "collocation",
    "phrase",
)


class CardRequestError(ValueError):
    """The submitted payload cannot be written; ``problems`` explains why."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__(problems[0])
        self.problems = problems


def lookup(card_type: str, text: str, config: AddonConfig) -> dict[str, Any]:
    """Run the add-on lookup for ``card_type``; raises ``OpenAIError``."""
    kwargs = chat_kwargs(config)
    if card_type == "normal":
        return _grouped(text, lookup_normal_grouped(text, **kwargs))
    if card_type == "word_pattern":
        return dict(lookup_word_pattern(text, **kwargs))
    if card_type == "vietnamese":
        return dict(lookup_vietnamese_word(text, **kwargs))
    if card_type == "sentence":
        # The dialog pre-fills the English side with the looked-up sentence.
        return {**lookup_sentence(text, **kwargs), "sentence": text.strip()}
    if card_type == "collocation":
        return dict(lookup_collocations(text, **kwargs))
    if card_type == "phrase":
        return dict(lookup_phrase(text, **kwargs))
    raise CardRequestError([f"Unknown card type: {card_type}"])


def _grouped(text: str, payload: Any) -> dict[str, Any]:
    """Root senses as groups (first-seen order), plus the root's family."""
    groups: dict[int, list[dict[str, Any]]] = {}
    for result in payload["results"]:
        sense = {key: value for key, value in result.items() if key != "group"}
        groups.setdefault(result["group"], []).append(sense)
    return {
        # What was typed is known here; don't rely on the model echoing it.
        "input": text.strip(),
        "word": payload["word"],
        "inputNote": payload["inputNote"],
        "groups": list(groups.values()),
        "family": payload["family"],
    }


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
        # Root senses grouped per card (see _grouped), plus picked family.
        groups = payload.get("groups")
        family = payload.get("family", [])
        if not isinstance(groups, list) or not all(isinstance(g, list) for g in groups):
            raise CardRequestError(["Invalid payload: groups must be a list of lists."])
        if not isinstance(family, list):
            raise CardRequestError(["Invalid payload: family must be a list."])
        _require_no_problems(normal_problems(groups, _dicts(family)))
        _validated(
            {"word": payload.get("word"), "results": [s for g in groups for s in g]},
            validate_normal_payload,
        )
        _validated(
            {"query": payload.get("word"), "results": family},
            validate_vietnamese_payload,
        )
        payload = {**payload, "family": family}
    elif card_type == "vietnamese":
        _require_no_problems(vietnamese_problems(_dicts(payload.get("results"))))
        _validated(payload, validate_vietnamese_payload)
    elif card_type == "word_pattern":
        _validated(payload, validate_word_pattern_payload)
        _require_no_problems(word_pattern_problems(payload))  # type: ignore[arg-type]
    elif card_type == "sentence":
        _validated(payload, _sentence)
        payload = {key: payload[key].strip() for key in ("vietnamese", "sentence")}
        _require_no_problems(
            sentence_problems(payload["vietnamese"], payload["sentence"])
        )
    elif card_type == "collocation":
        _require_no_problems(collocation_problems(_dicts(payload.get("items"))))
        _validated(payload, validate_collocation_payload)
    elif card_type == "phrase":
        phrase = payload.get("phrase")
        _require_no_problems(
            phrase_problems(
                phrase if isinstance(phrase, str) else "",
                _dicts(payload.get("results")),
            )
        )
        _validated(payload, validate_phrase_payload)
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
        groups = payload["groups"]
        # One clip per part of speech, then split back into the groups.
        flat = [sense for group in groups for sense in group]
        tags = iter(definition_audio_tags(word, flat, config, write_data, on_progress))
        grouped_tags = [[next(tags) for _sense in group] for group in groups]
        added = add_definition_group_notes(col, deck_id, word, groups, grouped_tags)
        # Family members are whole words of their own, one card each, written
        # the way Vietnamese -> English results are.
        family = payload["family"]
        family_tags = definition_audio_tags("", family, config, write_data, on_progress)
        return added + add_definition_notes(col, deck_id, "", "", "", family_tags, family)
    if card_type == "vietnamese":
        results = payload["results"]
        tags = definition_audio_tags("", results, config, write_data, on_progress)
        return add_definition_notes(col, deck_id, "", "", "", tags, results)
    if card_type == "word_pattern":
        return add_word_pattern_note(col, deck_id, payload)
    if card_type == "sentence":
        return add_sentence_note(
            col, deck_id, payload["vietnamese"], payload["sentence"]
        )
    if card_type == "collocation":
        return add_collocation_notes(
            col, deck_id, payload["keyword"].strip(), payload["items"]
        )
    if card_type == "phrase":
        return add_phrase_notes(
            col, deck_id, payload["phrase"].strip(), payload["results"]
        )
    raise CardRequestError([f"Unknown card type: {card_type}"])
