from anki_card_creator.create_checks import (
    definition_problems,
    problems_message,
    sentence_problems,
    vietnamese_problems,
    word_form_problems,
    word_pattern_problems,
)


def _form(word, pos, definition="d", vietnamese="v", examples=("e",)):
    return {
        "word": word,
        "type": pos,
        "definition": definition,
        "vietnamese": vietnamese,
        "examples": list(examples),
        "ipa": "",
        "popularity": None,
        "difficulty": None,
    }


def test_definition_and_vietnamese_need_a_selection():
    assert definition_problems([]) == ["Select at least one definition."]
    assert definition_problems([{"definition": "x"}]) == []
    assert vietnamese_problems([]) == ["Select at least one English word."]
    assert vietnamese_problems([{"word": "decide"}, {"word": " "}]) == [
        "Each selected result needs a word:",
        "result 2",
    ]


def test_word_form_lists_incomplete_members():
    payload = {
        "rootWord": _form("decide", "verb", examples=()),
        "other": [_form("decision", "noun"), _form("decisive", "adjective", vietnamese="")],
    }
    problems = word_form_problems(payload)
    assert problems[1:] == ["root word", "decisive (adjective)"]
    assert problems_message(problems).endswith("• root word\n• decisive (adjective)")
    assert word_form_problems({"rootWord": _form("decide", "verb"), "other": []}) == [
        "Root word and one related form are required."
    ]
    complete = {"rootWord": _form("decide", "verb"), "other": [_form("decision", "noun")]}
    assert word_form_problems(complete) == []


def test_pattern_and_sentence_require_both_sides():
    assert word_pattern_problems({"gap": "a", "answer": ""}) == [
        "Gap and answer are required."
    ]
    assert word_pattern_problems({"gap": "a", "answer": "b"}) == []
    assert sentence_problems("xin chào", " ") == [
        "Vietnamese meaning and English sentence are required."
    ]
    assert sentence_problems("xin chào", "hello") == []
