from __future__ import annotations

from typing import Any

NOTE_TYPE_NAME = "VIP Sentence"
FIELDS = ("Vietnamese", "Sentence")
CARD_FRONT = '<div class="definition-prompt">{{Vietnamese}}</div>'
CARD_BACK = (
    "{{FrontSide}}\n"
    '<hr class="divider" id="answer">\n'
    '<div class="section section-answer"><span class="section-label">English</span>'
    '<div class="value">{{Sentence}}</div></div>'
)


def add_sentence_note(
    col: Any, deck_id: int, vietnamese: str, sentence: str
) -> int:
    from .registry import ensure_note_type

    model = ensure_note_type(col, NOTE_TYPE_NAME, FIELDS, CARD_FRONT, CARD_BACK)
    note = col.new_note(model)
    note["Vietnamese"] = vietnamese
    note["Sentence"] = sentence
    col.add_note(note, deck_id)
    return 1
