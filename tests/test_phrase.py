from typing import get_type_hints

import pytest

from anki_card_creator.create_checks import phrase_problems
from anki_card_creator.lookups.contracts import PhraseSense, validate_phrase_payload
from anki_card_creator.lookups.schemas import PHRASE_SENSE
from anki_card_creator.notes.phrase import phrase_hint


def _sense(**overrides):
    sense = {
        "structure": "adjective + noun",
        "definition": "a sudden, large decrease",
        "vietnamese": "sự giảm mạnh",
        "examples": ["Shares saw a sharp fall in early trading."],
        "usage": "news, business",
    }
    return {**sense, **overrides}


def test_sense_contract_matches_schema():
    assert set(get_type_hints(PhraseSense)) == set(PHRASE_SENSE["properties"])
    assert set(PHRASE_SENSE["required"]) == set(PHRASE_SENSE["properties"])


def test_validator_requires_phrase_and_definitions():
    payload = {"phrase": "sharp fall", "results": [_sense()]}
    assert validate_phrase_payload(payload) is payload
    with pytest.raises(ValueError, match="phrase"):
        validate_phrase_payload({"phrase": " ", "results": []})
    with pytest.raises(ValueError, match="definition"):
        validate_phrase_payload({"phrase": "sharp fall", "results": [_sense(definition="")]})
    with pytest.raises(ValueError, match="examples"):
        validate_phrase_payload({"phrase": "sharp fall", "results": [_sense(examples="x")]})


def test_create_checks():
    assert phrase_problems("", [_sense()]) == ["Enter the phrase."]
    assert phrase_problems("sharp fall", []) == ["Select at least one meaning."]
    assert phrase_problems("sharp fall", [_sense()]) == []
    assert phrase_problems("sharp fall", [_sense(), _sense(definition=" ")]) == [
        "Each selected meaning needs a definition:",
        "meaning 2",
    ]


@pytest.mark.parametrize(
    ("phrase", "hint"),
    [
        ("sharp fall", "s___ f___"),
        ("well-known fact", "w___ f___"),
        ("a far cry", "a___ f___ c___"),
        ("  run   out ", "r___ o___"),
    ],
)
def test_hint_keeps_first_letters(phrase, hint):
    assert phrase_hint(phrase) == hint
