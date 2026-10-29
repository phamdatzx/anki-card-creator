from __future__ import annotations

from typing import Any

from ..lookups.contracts import DefinitionResult
from .shared import examples_html, join_values
from .word_form import pos_abbrev

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
    '<div class="definition-prompt">{{Definition}}</div>\n'
    '{{#Vietnamese}}<div class="definition-vietnamese">{{Vietnamese}}</div>{{/Vietnamese}}'
)
CARD_BACK = (
    "{{FrontSide}}\n"
    '<hr class="divider" id="answer">\n'
    '<div class="section section-word"><span class="section-label">Word</span>'
    '<div class="value">{{Word}} {{Audio}}</div></div>\n'
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
    note["Word"] = str(result.get("word") or word)
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


def _abbrev(result: DefinitionResult) -> str:
    return pos_abbrev(str(result.get("partOfSpeech") or "")).lower()


def merged_fields(
    word: str, results: list[DefinitionResult], audio_tags: list[str]
) -> dict[str, str]:
    """Field values for one note covering related senses of several POS.

    Uses the same VIP Translate fields as a one-sense note, so templates and
    existing cards are unchanged: each part is a badge line in Definition, and
    the other fields label their entries with the part's abbreviation.
    """
    ipas = [str(r.get("ipa") or "").strip() for r in results]
    distinct = [ipa for ipa in dict.fromkeys(ipas) if ipa]
    if len(distinct) > 1:
        pronunciation = " · ".join(
            f"({_abbrev(r)}) {ipa}" for r, ipa in zip(results, ipas, strict=True) if ipa
        )
    else:
        pronunciation = distinct[0] if distinct else ""
    return {
        "Word": word,
        "Pronunciation": pronunciation,
        "SyllableCount": "",
        "PartOfSpeech": "",
        "Definition": "".join(
            f'<div class="sense-line"><span class="badge">{r.get("partOfSpeech") or "?"}</span> '
            f"{r.get('definition') or ''}</div>"
            for r in results
        ),
        "Vietnamese": " · ".join(
            f"({_abbrev(r)}) {r.get('vietnamese')}"
            for r in results
            if str(r.get("vietnamese") or "").strip()
        ),
        "Synonyms": join_values(
            list(dict.fromkeys(s for r in results for s in r.get("synonyms") or []))
        ),
        "Examples": examples_html(
            [f"({_abbrev(r)}) {example}" for r in results for example in r.get("examples") or []]
        ),
        "Audio": " ".join(dict.fromkeys(tag for tag in audio_tags if tag)),
    }


def add_definition_group_notes(
    col: Any,
    deck_id: int,
    word: str,
    groups: list[list[DefinitionResult]],
    audio_tags: list[list[str]],
) -> int:
    """One VIP Translate note per group (Word Inbox's grouped Normal cards).

    A one-sense group is written exactly like ``add_definition_notes`` does.
    """
    if [len(group) for group in groups] != [len(tags) for tags in audio_tags]:
        raise ValueError("Each definition needs one pronunciation clip.")
    from .registry import ensure_note_type

    model = ensure_note_type(col, NOTE_TYPE_NAME, FIELDS, CARD_FRONT, CARD_BACK)
    for group, tags in zip(groups, audio_tags, strict=True):
        if len(group) == 1:
            note = build_note(col, model, word, "", "", tags[0], group[0])
        else:
            note = col.new_note(model)
            for field, value in merged_fields(word, group, tags).items():
                note[field] = value
        col.add_note(note, deck_id)
    return len(groups)
