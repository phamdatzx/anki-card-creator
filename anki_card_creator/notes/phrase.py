from __future__ import annotations

from typing import Any

from ..lookups.contracts import PhraseSense
from .shared import examples_html

NOTE_TYPE_NAME = "VIP Phrase"
FIELDS = (
    "Phrase",
    "Structure",
    "Hint",
    "Definition",
    "Vietnamese",
    "Examples",
    "Usage",
)
CARD_FRONT = (
    '{{#Structure}}<div class="pos-line"><span class="badge">{{Structure}}</span></div>{{/Structure}}\n'
    '<div class="definition-prompt">{{Definition}}</div>\n'
    '{{#Vietnamese}}<div class="definition-vietnamese">({{Vietnamese}})</div>{{/Vietnamese}}\n'
    '{{#Hint}}<div class="gap-prompt">{{Hint}}</div>{{/Hint}}'
)
CARD_BACK = (
    "{{FrontSide}}\n"
    '<hr class="divider" id="answer">\n'
    '<div class="section section-word"><span class="section-label">Phrase</span>'
    '<div class="value">{{Phrase}}</div></div>\n'
    '{{#Examples}}<div class="section"><span class="section-label">Examples</span>'
    "<div>{{Examples}}</div></div>{{/Examples}}\n"
    '{{#Usage}}<div class="section section-meta"><span class="section-label">Usage</span>'
    '<div class="meta-row">{{Usage}}</div></div>{{/Usage}}'
)


def phrase_hint(phrase: str) -> str:
    """First letter of each word plus a blank: "sharp fall" -> "s___ f___".

    Hyphens and apostrophes stay inside a word ("well-known" -> "w___").
    """
    return " ".join(f"{word[0]}___" for word in phrase.split())


def add_phrase_notes(
    col: Any, deck_id: int, phrase: str, senses: list[PhraseSense]
) -> int:
    from .registry import ensure_note_type

    model = ensure_note_type(col, NOTE_TYPE_NAME, FIELDS, CARD_FRONT, CARD_BACK)
    for sense in senses:
        note = col.new_note(model)
        note["Phrase"] = phrase
        note["Structure"] = str(sense.get("structure") or "")
        note["Hint"] = phrase_hint(phrase)
        note["Definition"] = str(sense.get("definition") or "")
        note["Vietnamese"] = str(sense.get("vietnamese") or "")
        note["Examples"] = examples_html(sense.get("examples"))
        note["Usage"] = str(sense.get("usage") or "")
        col.add_note(note, deck_id)
    return len(senses)
