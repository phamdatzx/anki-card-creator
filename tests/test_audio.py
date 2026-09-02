from anki_card_creator.audio import (
    definition_audio_key,
    form_audio_key,
    tts_instructions,
    unique_forms,
)


def test_tts_instructions_use_first_example_and_ipa():
    text = tts_instructions(
        part_of_speech="verb",
        definition="to register",
        examples=["Please record this.", "A second example."],
        ipa="/rɪˈkɔrd/",
    )
    assert "verb sense" in text
    assert 'Intended definition: "to register".' in text
    assert "/rɪˈkɔrd/" in text
    assert "Please record this." in text
    assert "A second example." not in text


def test_audio_keys_normalize_case_and_whitespace():
    assert form_audio_key(" Word ", " Noun ") == ("word", "noun")
    assert definition_audio_key(
        " Record ", {"partOfSpeech": " Verb ", "definition": " Save "}
    ) == ("record", "verb", "save")


def test_unique_forms_deduplicates_without_reordering():
    forms = [
        {"word": "ability", "type": "noun", "ipa": "/a/"},
        {"word": "Ability", "type": "NOUN", "ipa": "/ignored/"},
        {"word": "enable", "type": "verb"},
    ]
    unique = unique_forms(forms)
    assert list(unique) == [("ability", "noun"), ("enable", "verb")]
    assert unique[("ability", "noun")][3] == "/a/"
