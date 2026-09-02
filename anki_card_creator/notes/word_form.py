from __future__ import annotations

from typing import Any

from ..audio_keys import AudioKey, form_audio_key
from ..lookups.contracts import WordFormItem, WordFormPayload
from .shared import audio_control

NOTE_TYPE_NAME = "VIP Word Form"
FIELDS = (
    "FrontSummary",
    "RootWord",
    "RootType",
    "Pronunciation",
    "RootDefinition",
    "RootVietnamese",
    "FamilyHtml",
    "Audio",
    "FrontAudio",
)
CARD_FRONT = (
    '<div class="prompt">{{FrontSummary}}</div>\n'
    '<div class="prompt-audio">{{FrontAudio}}</div>'
)
CARD_BACK = (
    '<div class="prompt">{{FrontSummary}}</div>\n'
    '<hr class="divider" id="answer">\n'
    '{{#FamilyHtml}}<div class="section"><span class="section-label">Related forms</span>'
    '<div class="family">{{FamilyHtml}}</div></div>{{/FamilyHtml}}\n'
    '<div class="section section-word"><span class="section-label">Root</span>'
    '<div class="value">{{RootWord}} <span class="badge">{{RootType}}</span> {{Audio}}</div></div>\n'
    '{{#RootVietnamese}}<div class="section"><span class="section-label">Vietnamese</span>'
    "<div>{{RootVietnamese}}</div></div>{{/RootVietnamese}}\n"
    '{{#Pronunciation}}<div class="section section-meta"><span class="section-label">Pronunciation</span>'
    '<div class="meta-row">{{Pronunciation}}</div></div>{{/Pronunciation}}\n'
    '{{#RootDefinition}}<div class="section"><span class="section-label">Root definition</span>'
    "<div>{{RootDefinition}}</div></div>{{/RootDefinition}}"
)

POS_ABBREV = {
    "noun": "N",
    "verb": "V",
    "adjective": "adj",
    "adverb": "adv",
    "preposition": "prep",
    "conjunction": "conj",
    "interjection": "interj",
    "pronoun": "pron",
    "determiner": "det",
}


def pos_abbrev(pos: str) -> str:
    cleaned = (pos or "").strip()
    return POS_ABBREV.get(cleaned.lower(), cleaned) if cleaned else "?"


def format_pos_count(count: int, abbrev: str) -> str:
    return f"{count}{abbrev}" if len(abbrev) <= 1 else f"{count} {abbrev}"


def group_others_by_type(
    others: list[WordFormItem],
) -> list[tuple[str, list[WordFormItem]]]:
    groups: dict[str, list[WordFormItem]] = {}
    order: list[str] = []
    for item in others:
        key = str(item.get("type") or "").strip().lower() or "?"
        if key not in groups:
            order.append(key)
            groups[key] = []
        groups[key].append(item)
    return [(key, groups[key]) for key in order]


def word_form_card_summaries(payload: WordFormPayload) -> list[str]:
    root = payload.get("rootWord") or {}
    root_label = (
        f"{root.get('word') or ''!s} "
        f"({pos_abbrev(str(root.get('type') or ''))})"
    )
    summaries = []
    for _key, items in group_others_by_type(list(payload.get("other") or [])):
        abbreviation = pos_abbrev(str(items[0].get("type") or ""))
        summaries.append(
            f"{root_label}, {format_pos_count(len(items), abbreviation)}"
        )
    return summaries


def word_form_front_html(root_word: str, root_type: str, count_label: str) -> str:
    return (
        f'<div class="prompt-root">{root_word}'
        f'<span class="badge">{pos_abbrev(root_type)}</span></div>'
        f'<div class="prompt-target">{count_label}</div>'
    )


def word_form_family_html(
    others: list[WordFormItem], audio_by_form: dict[AudioKey, str]
) -> str:
    lines = []
    for item in others:
        word = str(item.get("word") or "")
        pos = str(item.get("type") or "")
        audio = audio_control(audio_by_form.get(form_audio_key(word, pos), ""))
        block = (
            '<div class="family-item">'
            f'<div class="family-word">{word}'
            f'<span class="badge">{pos}</span> {audio}</div>'
        )
        if item.get("special_definition"):
            block += (
                f'<div class="family-special">{item["special_definition"]}</div>'
            )
        if item.get("ipa"):
            block += f'<div class="family-ipa">{item["ipa"]}</div>'
        lines.append(block + "</div>")
    return "\n".join(lines)


def add_word_form_notes(
    col: Any,
    deck_id: int,
    payload: WordFormPayload,
    root_audio: str,
    audio_by_form: dict[AudioKey, str],
) -> int:
    from .registry import ensure_note_type

    model = ensure_note_type(col, NOTE_TYPE_NAME, FIELDS, CARD_FRONT, CARD_BACK)
    root = payload.get("rootWord") or {}
    groups = group_others_by_type(list(payload.get("other") or []))
    for _key, items in groups:
        count_label = format_pos_count(
            len(items), pos_abbrev(str(items[0].get("type") or ""))
        )
        note = col.new_note(model)
        note["FrontSummary"] = word_form_front_html(
            str(root.get("word") or ""), str(root.get("type") or ""), count_label
        )
        note["RootWord"] = str(root.get("word") or "")
        note["RootType"] = str(root.get("type") or "")
        note["Pronunciation"] = str(root.get("ipa") or "")
        note["RootDefinition"] = str(root.get("definition") or "")
        note["RootVietnamese"] = str(root.get("vietnamese") or "")
        note["FamilyHtml"] = word_form_family_html(items, audio_by_form)
        note["Audio"] = audio_control(root_audio)
        note["FrontAudio"] = root_audio
        col.add_note(note, deck_id)
    return len(groups)
