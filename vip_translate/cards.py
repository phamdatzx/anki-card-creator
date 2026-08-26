from __future__ import annotations

from typing import Any

from anki.collection import Collection
from anki.models import NotetypeDict
from anki.notes import Note

NOTE_TYPE_NAME = "VIP Translate"
FIELDS = (
    "Word",
    "Pronunciation",
    "SyllableCount",
    "PartOfSpeech",
    "Definition",
    "Synonyms",
    "Examples",
)

CARD_FRONT = (
    '{{#PartOfSpeech}}<div class="pos">{{PartOfSpeech}}</div>{{/PartOfSpeech}}\n'
    '<div class="definition">{{Definition}}</div>'
)

CARD_BACK = (
    "{{FrontSide}}\n"
    '<hr id="answer">\n'
    '<div class="word">{{Word}}</div>\n'
    '{{#Pronunciation}}<div class="pron">{{Pronunciation}}</div>{{/Pronunciation}}\n'
    '{{#SyllableCount}}<div class="syllables">{{SyllableCount}} syllables</div>{{/SyllableCount}}\n'
    '{{#Synonyms}}<div class="synonyms"><b>Synonyms:</b> {{Synonyms}}</div>{{/Synonyms}}\n'
    '{{#Examples}}<div class="examples"><b>Examples:</b> {{Examples}}</div>{{/Examples}}'
)


def ensure_note_type(col: Collection) -> NotetypeDict:
    model = col.models.by_name(NOTE_TYPE_NAME)
    if model is None:
        model = col.models.new(NOTE_TYPE_NAME)
        for name in FIELDS:
            col.models.add_field(model, col.models.new_field(name))
        template = col.models.new_template("Card 1")
        template["qfmt"] = CARD_FRONT
        template["afmt"] = CARD_BACK
        col.models.add_template(model, template)
        col.models.add(model)
        return model

    existing_names = {field["name"] for field in model["flds"]}
    for name in FIELDS:
        if name not in existing_names:
            col.models.add_field(model, col.models.new_field(name))
    if model["tmpls"]:
        model["tmpls"][0]["qfmt"] = CARD_FRONT
        model["tmpls"][0]["afmt"] = CARD_BACK
    col.models.update_dict(model)
    return model


def _join(values: Any) -> str:
    if not values:
        return ""
    if isinstance(values, str):
        return values
    return ", ".join(str(v) for v in values if v)


def build_note(
    col: Collection,
    model: NotetypeDict,
    word: str,
    pronunciation: str,
    syllable_count: str,
    result: dict[str, Any],
) -> Note:
    note = col.new_note(model)
    note["Word"] = word
    note["Pronunciation"] = pronunciation
    note["SyllableCount"] = syllable_count
    note["PartOfSpeech"] = str(result.get("partOfSpeech") or "")
    note["Definition"] = str(result.get("definition") or "")
    note["Synonyms"] = _join(result.get("synonyms"))
    note["Examples"] = _join(result.get("examples"))
    return note


def add_definition_notes(
    col: Collection,
    deck_id: int,
    word: str,
    pronunciation: str,
    syllable_count: str,
    results: list[dict[str, Any]],
) -> int:
    model = ensure_note_type(col)
    added = 0
    for result in results:
        note = build_note(
            col, model, word, pronunciation, syllable_count, result
        )
        col.add_note(note, deck_id)
        added += 1
    return added
