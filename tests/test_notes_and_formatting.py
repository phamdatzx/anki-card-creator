from anki_card_creator.notes.shared import audio_control, examples_html
from anki_card_creator.notes.word_form import (
    group_others_by_type,
    word_form_card_summaries,
    word_form_family_html,
)
from anki_card_creator.text import as_text, parse_score, split_list


def test_text_list_and_score_helpers():
    assert as_text(["a", "b"]) == "a, b"
    assert as_text(["a", "b"], multiline=True) == "a\nb"
    assert split_list("a\nb", multiline=True) == ["a", "b"]
    assert parse_score("4") == 4
    assert parse_score("bad") is None


def test_word_form_grouping_preserves_first_seen_order():
    forms = [
        {"word": "enable", "type": "verb"},
        {"word": "ability", "type": "noun"},
        {"word": "disable", "type": "Verb"},
    ]
    groups = group_others_by_type(forms)
    assert [key for key, _items in groups] == ["verb", "noun"]
    assert [item["word"] for item in groups[0][1]] == ["enable", "disable"]


def test_word_form_summary_and_stored_html():
    payload = {
        "rootWord": {"word": "able", "type": "adjective"},
        "other": [
            {"word": "ability", "type": "noun"},
            {"word": "inability", "type": "noun"},
        ],
    }
    assert word_form_card_summaries(payload) == ["able (adj), 2N"]
    html = word_form_family_html(
        payload["other"], {("ability", "noun"): "[sound:ability.mp3]"}
    )
    assert html.index("ability") < html.index("inability")
    assert 'src="ability.mp3"' in html
    assert examples_html(["One.", "Two."]) == (
        '<ul class="examples-list"><li>One.</li><li>Two.</li></ul>'
    )
    assert audio_control("[sound:a&amp;b.mp3]") == (
        '<audio class="audio-control" controls preload="none" '
        'src="a&amp;amp;b.mp3"></audio>'
    )
