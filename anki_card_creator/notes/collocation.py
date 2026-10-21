from __future__ import annotations

from typing import Any

from ..lookups.contracts import GAP_MARK, CollocationItem

NOTE_TYPE_NAME = "VIP Collocation"
FIELDS = (
    "Keyword",
    "Pattern",
    "Gap",
    "Answer",
    "Collocation",
    "Vietnamese",
    "Sentence",
    "Usage",
)
CARD_FRONT = (
    '{{#Pattern}}<div class="pos-line"><span class="badge">{{Pattern}}</span></div>{{/Pattern}}\n'
    '<div class="gap-prompt">{{Gap}}</div>\n'
    '{{#Vietnamese}}<div class="definition-vietnamese">({{Vietnamese}})</div>{{/Vietnamese}}'
)
CARD_BACK = (
    "{{FrontSide}}\n"
    '<hr class="divider" id="answer">\n'
    '<div class="section section-answer"><span class="section-label">Answer</span>'
    '<div class="value">{{Answer}}</div></div>\n'
    '<div class="section"><span class="section-label">Collocation</span>'
    "<div>{{Collocation}}</div></div>\n"
    '{{#Sentence}}<div class="section"><span class="section-label">Sentence</span>'
    "<div>{{Sentence}}</div></div>{{/Sentence}}\n"
    '{{#Usage}}<div class="section section-meta"><span class="section-label">Usage</span>'
    '<div class="meta-row">{{Usage}}</div></div>{{/Usage}}'
)


def filled_sentence(gap: str, answer: str) -> str:
    """The gap sentence with the answer put back in, in bold."""
    before, _, after = gap.partition(GAP_MARK)
    return f"{before}<b>{answer}</b>{after}"


def add_collocation_notes(
    col: Any, deck_id: int, keyword: str, items: list[CollocationItem]
) -> int:
    from .registry import ensure_note_type

    model = ensure_note_type(col, NOTE_TYPE_NAME, FIELDS, CARD_FRONT, CARD_BACK)
    for item in items:
        gap = str(item.get("gap") or "")
        answer = str(item.get("answer") or "")
        note = col.new_note(model)
        note["Keyword"] = keyword
        note["Pattern"] = str(item.get("pattern") or "")
        note["Gap"] = gap
        note["Answer"] = answer
        note["Collocation"] = str(item.get("collocation") or "")
        note["Vietnamese"] = str(item.get("vietnamese") or "")
        note["Sentence"] = filled_sentence(gap, answer)
        note["Usage"] = str(item.get("usage") or "")
        col.add_note(note, deck_id)
    return len(items)
