from typing import get_type_hints

import pytest

from anki_card_creator.create_checks import definition_group_problems
from anki_card_creator.lookups.contracts import (
    GroupedDefinitionResult,
    NormalGroupedPayload,
    validate_normal_grouped_payload,
)
from anki_card_creator.lookups.schemas import (
    GROUPED_DEFINITION_RESULT,
    NORMAL_GROUPED_SCHEMA,
)
from anki_card_creator.notes.normal import merged_fields


def _sense(pos="verb", ipa="/test/", **overrides):
    sense = {
        "definition": f"{pos} meaning",
        "vietnamese": f"vi {pos}",
        "partOfSpeech": pos,
        "ipa": ipa,
        "synonyms": ["check"],
        "examples": [f"A {pos} example."],
        "popularity": 3,
        "difficulty": 2,
    }
    return {**sense, **overrides}


def test_grouped_contract_matches_schema():
    assert set(get_type_hints(GroupedDefinitionResult)) == set(
        GROUPED_DEFINITION_RESULT["properties"]
    )
    assert set(GROUPED_DEFINITION_RESULT["required"]) == set(
        GROUPED_DEFINITION_RESULT["properties"]
    )
    assert set(get_type_hints(NormalGroupedPayload)) == set(
        NORMAL_GROUPED_SCHEMA["properties"]
    )


@pytest.mark.parametrize("group", [0, -1, "1", True, None])
def test_validator_needs_a_positive_group(group):
    payload = {"word": "test", "results": [{**_sense(), "group": group}]}
    with pytest.raises(ValueError, match="group must be a positive integer"):
        validate_normal_grouped_payload(payload)
    ok = {"word": "test", "results": [{**_sense(), "group": 1}]}
    assert validate_normal_grouped_payload(ok) is ok


def test_group_problems():
    assert definition_group_problems([]) == ["Select at least one definition."]
    assert definition_group_problems([[_sense()], []]) == [
        "Each selected card needs at least one part of speech."
    ]
    assert definition_group_problems([[_sense(), _sense("noun")]]) == []


def test_merged_fields_label_each_part():
    fields = merged_fields(
        "record",
        [
            _sense("noun", "/ˈrekərd/", synonyms=["log", "file"]),
            _sense("verb", "/rɪˈkɔːrd/", synonyms=["log", "note"]),
        ],
        ["[sound:a.mp3]", "[sound:b.mp3]"],
    )
    assert fields["PartOfSpeech"] == ""
    assert fields["Definition"] == (
        '<div class="sense-line"><span class="badge">noun</span> noun meaning</div>'
        '<div class="sense-line"><span class="badge">verb</span> verb meaning</div>'
    )
    assert fields["Vietnamese"] == "(n) vi noun · (v) vi verb"
    assert fields["Pronunciation"] == "(n) /ˈrekərd/ · (v) /rɪˈkɔːrd/"
    assert fields["Synonyms"] == "log, file, note"
    assert "<li>(v) A verb example.</li>" in fields["Examples"]
    assert fields["Audio"] == "[sound:a.mp3] [sound:b.mp3]"


def test_merged_fields_share_one_ipa_and_skip_blanks():
    fields = merged_fields(
        "test",
        [_sense("verb"), _sense("noun", vietnamese="", ipa="/test/")],
        ["[sound:a.mp3]", "[sound:a.mp3]"],
    )
    assert fields["Pronunciation"] == "/test/"
    assert fields["Vietnamese"] == "(v) vi verb"
    assert fields["Audio"] == "[sound:a.mp3]"
