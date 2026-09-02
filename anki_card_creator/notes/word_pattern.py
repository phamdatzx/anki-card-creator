from __future__ import annotations

from typing import Any

from ..lookups.contracts import WordPatternPayload
from .shared import examples_html

NOTE_TYPE_NAME = "VIP Word Pattern"
FIELDS = ("Gap", "Vietnamese", "Answer", "Pattern", "Explanation", "Examples")
CARD_FRONT = '<div class="gap-prompt">{{Gap}}</div>'
CARD_BACK = (
    "{{FrontSide}}\n"
    '<hr class="divider" id="answer">\n'
    '<div class="section section-answer"><span class="section-label">Answer</span>'
    '<div class="value">{{Answer}}</div></div>\n'
    '{{#Vietnamese}}<div class="section"><span class="section-label">Vietnamese</span>'
    "<div>{{Vietnamese}}</div></div>{{/Vietnamese}}\n"
    '{{#Pattern}}<div class="section"><span class="section-label">Pattern</span>'
    "<div>{{Pattern}}</div></div>{{/Pattern}}\n"
    '{{#Explanation}}<div class="section"><span class="section-label">Explanation</span>'
    "<div>{{Explanation}}</div></div>{{/Explanation}}\n"
    '{{#Examples}}<div class="section"><span class="section-label">Examples</span>'
    "<div>{{Examples}}</div></div>{{/Examples}}"
)


def add_word_pattern_note(
    col: Any, deck_id: int, payload: WordPatternPayload
) -> int:
    from .registry import ensure_note_type

    model = ensure_note_type(col, NOTE_TYPE_NAME, FIELDS, CARD_FRONT, CARD_BACK)
    note = col.new_note(model)
    note["Gap"] = str(payload.get("gap") or "")
    note["Vietnamese"] = str(payload.get("vietnamese") or "")
    note["Answer"] = str(payload.get("answer") or "")
    note["Pattern"] = str(payload.get("pattern") or "")
    note["Explanation"] = str(payload.get("explanation") or "")
    note["Examples"] = examples_html(payload.get("examples"))
    col.add_note(note, deck_id)
    return 1
