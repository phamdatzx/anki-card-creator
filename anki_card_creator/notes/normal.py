from __future__ import annotations

from typing import Any

from ..lookups.contracts import DefinitionResult
from .shared import examples_html, join_values

NOTE_TYPE_NAME = "VIP Translate"
FIELDS = (
    "Word",
    "Pronunciation",
    "SyllableCount",
    "PartOfSpeech",
    "Definition",
    "Vietnamese",
    "Synonyms",
    "Examples",
    "Audio",
)
CARD_FRONT = (
    '{{#PartOfSpeech}}<div class="pos-line"><span class="badge">{{PartOfSpeech}}</span></div>{{/PartOfSpeech}}\n'
    '<div class="definition-prompt">{{Definition}}</div>'
)
CARD_BACK = (
    "{{FrontSide}}\n"
    '<hr class="divider" id="answer">\n'
    '<div class="section section-word"><span class="section-label">Word</span>'
    '<div class="value">{{Word}} {{Audio}}</div></div>\n'
    '{{#Vietnamese}}<div class="section"><span class="section-label">Vietnamese</span>'
    "<div>{{Vietnamese}}</div></div>{{/Vietnamese}}\n"
    '{{#Pronunciation}}<div class="section section-meta"><span class="section-label">Pronunciation</span>'
    '<div class="meta-row">{{Pronunciation}}</div></div>{{/Pronunciation}}\n'
    '{{#SyllableCount}}<div class="section section-meta"><span class="section-label">Syllables</span>'
    '<div class="meta-row">{{SyllableCount}}</div></div>{{/SyllableCount}}\n'
    '{{#Synonyms}}<div class="section"><span class="section-label">Synonyms</span>'
    "<div>{{Synonyms}}</div></div>{{/Synonyms}}\n"
    '{{#Examples}}<div class="section"><span class="section-label">Examples</span>'
    "<div>{{Examples}}</div></div>{{/Examples}}"
)


def build_note(
    col: Any,
    model: Any,
    word: str,
    pronunciation: str,
    syllable_count: str,
    audio: str,
    result: DefinitionResult,
) -> Any:
    note = col.new_note(model)
    note["Word"] = word
    note["Pronunciation"] = str(result.get("ipa") or pronunciation)
    note["SyllableCount"] = syllable_count
    note["Audio"] = audio
    note["PartOfSpeech"] = str(result.get("partOfSpeech") or "")
    note["Definition"] = str(result.get("definition") or "")
    note["Vietnamese"] = str(result.get("vietnamese") or "")
    note["Synonyms"] = join_values(result.get("synonyms"))
    note["Examples"] = examples_html(result.get("examples"))
    return note


def add_definition_notes(
    col: Any,
    deck_id: int,
    word: str,
    pronunciation: str,
    syllable_count: str,
    audio_tags: list[str],
    results: list[DefinitionResult],
) -> int:
    if len(audio_tags) != len(results):
        raise ValueError("Each definition needs one pronunciation clip.")
    from .registry import ensure_note_type

    model = ensure_note_type(col, NOTE_TYPE_NAME, FIELDS, CARD_FRONT, CARD_BACK)
    for result, audio in zip(results, audio_tags, strict=True):
        col.add_note(
            build_note(
                col, model, word, pronunciation, syllable_count, audio, result
            ),
            deck_id,
        )
    return len(results)
