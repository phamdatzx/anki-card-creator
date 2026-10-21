from typing import get_type_hints

import pytest

from anki_card_creator.create_checks import collocation_problems
from anki_card_creator.lookups.contracts import (
    CollocationItem,
    validate_collocation_payload,
)
from anki_card_creator.lookups.schemas import COLLOCATION_ITEM
from anki_card_creator.notes.collocation import FIELDS, filled_sentence


def _item(**overrides):
    item = {
        "pattern": "verb + decision",
        "collocation": "make a decision",
        "gap": "She finally ___ a decision to move abroad.",
        "answer": "made",
        "vietnamese": "đưa ra quyết định",
        "usage": "neutral, very common",
    }
    return {**item, **overrides}


def test_item_contract_matches_schema():
    assert set(get_type_hints(CollocationItem)) == set(COLLOCATION_ITEM["properties"])
    assert set(COLLOCATION_ITEM["required"]) == set(COLLOCATION_ITEM["properties"])


def test_validator_requires_exactly_one_gap():
    payload = {"keyword": "decision", "items": [_item()]}
    assert validate_collocation_payload(payload) is payload
    for gap in ("She made a decision.", "She ___ a ___."):
        with pytest.raises(ValueError, match="exactly one ___"):
            validate_collocation_payload({"keyword": "decision", "items": [_item(gap=gap)]})
    with pytest.raises(ValueError, match="answer"):
        validate_collocation_payload({"keyword": "decision", "items": [_item(answer=" ")]})
    with pytest.raises(ValueError, match="keyword"):
        validate_collocation_payload({"keyword": "", "items": []})


def test_create_checks_list_broken_items():
    assert collocation_problems([]) == ["Select at least one collocation."]
    assert collocation_problems([_item()]) == []
    problems = collocation_problems(
        [_item(), _item(collocation="reach a decision", gap="No gap here.")]
    )
    assert problems[1:] == ["reach a decision"]


def test_sentence_puts_the_answer_back():
    assert filled_sentence("She ___ a decision.", "made") == "She <b>made</b> a decision."
    assert "Sentence" in FIELDS and "Gap" in FIELDS
