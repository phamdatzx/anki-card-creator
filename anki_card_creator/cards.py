from __future__ import annotations

from typing import Any

from anki.collection import Collection
from anki.models import NotetypeDict
from anki.notes import Note

# Shared styling for study/review cards
CARD_CSS = """\
.card {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 18px;
  line-height: 1.45;
  color: #1a1a1a;
  background: #fafafa;
  text-align: left;
  padding: 1.25em 1.5em;
}
.nightMode .card { color: #ececec; background: #2b2b2b; }

.prompt {
  text-align: center;
  padding: 0.5em 0 0.25em;
}
.prompt-root {
  font-size: 1.35em;
  font-weight: 650;
  margin-bottom: 0.45em;
}
.prompt-target {
  display: inline-block;
  margin-top: 0.35em;
  padding: 0.25em 0.7em;
  border-radius: 6px;
  background: #e8eef5;
  font-size: 1.15em;
  font-weight: 650;
  letter-spacing: 0.02em;
}
.nightMode .prompt-target { background: #3a4554; }

.badge {
  display: inline-block;
  margin-left: 0.25em;
  padding: 0.05em 0.4em;
  border-radius: 4px;
  background: #ececec;
  font-size: 0.72em;
  font-weight: 600;
  vertical-align: middle;
  color: #444;
}
.nightMode .badge { background: #444; color: #ddd; }

.pos-line {
  text-align: center;
  margin-bottom: 0.6em;
}
.definition-prompt {
  text-align: center;
  font-size: 1.15em;
  line-height: 1.5;
}

.gap-prompt {
  text-align: center;
  font-size: 1.35em;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.divider {
  border: 0;
  border-top: 1px solid #d0d0d0;
  margin: 1.1em 0;
}
.nightMode .divider { border-top-color: #555; }

.section {
  margin: 0.85em 0;
  padding: 0.7em 0.9em;
  border-radius: 8px;
  background: #f0f0f0;
  border: 1px solid #e2e2e2;
}
.nightMode .section {
  background: #333;
  border-color: #444;
}
.section-label {
  display: block;
  margin-bottom: 0.35em;
  font-size: 0.72em;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: #666;
}
.nightMode .section-label { color: #aaa; }

.section-word .value {
  font-size: 1.4em;
  font-weight: 700;
}
.section-meta .meta-row {
  margin: 0.2em 0;
  color: #444;
}
.nightMode .section-meta .meta-row { color: #ccc; }

.section-answer .value {
  font-size: 1.35em;
  font-weight: 700;
  color: #0b5;
}
.nightMode .section-answer .value { color: #5d5; }

.family-item {
  padding: 0.55em 0;
  border-top: 1px solid #ddd;
}
.family-item:first-child { border-top: 0; padding-top: 0; }
.nightMode .family-item { border-top-color: #4a4a4a; }
.family-word {
  font-size: 1.05em;
  font-weight: 650;
}
.family-special {
  margin-top: 0.25em;
  font-size: 0.92em;
  color: #555;
}
.nightMode .family-special { color: #bbb; }

.examples-list {
  margin: 0.2em 0 0;
  padding-left: 1.15em;
}
.examples-list li { margin: 0.25em 0; }
"""

# --- Normal (WordsAPI) ---

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
    '{{#PartOfSpeech}}<div class="pos-line"><span class="badge">{{PartOfSpeech}}</span></div>{{/PartOfSpeech}}\n'
    '<div class="definition-prompt">{{Definition}}</div>'
)

CARD_BACK = (
    "{{FrontSide}}\n"
    '<hr class="divider" id="answer">\n'
    '<div class="section section-word">'
    '<span class="section-label">Word</span>'
    '<div class="value">{{Word}}</div>'
    "</div>\n"
    '{{#Pronunciation}}<div class="section section-meta">'
    '<span class="section-label">Pronunciation</span>'
    '<div class="meta-row">{{Pronunciation}}</div>'
    "</div>{{/Pronunciation}}\n"
    '{{#SyllableCount}}<div class="section section-meta">'
    '<span class="section-label">Syllables</span>'
    '<div class="meta-row">{{SyllableCount}}</div>'
    "</div>{{/SyllableCount}}\n"
    '{{#Synonyms}}<div class="section">'
    '<span class="section-label">Synonyms</span>'
    "<div>{{Synonyms}}</div>"
    "</div>{{/Synonyms}}\n"
    '{{#Examples}}<div class="section">'
    '<span class="section-label">Examples</span>'
    "<div>{{Examples}}</div>"
    "</div>{{/Examples}}"
)

# --- Phrasal verb ---

PHRASAL_NOTE_TYPE = "VIP Phrasal Verb"
PHRASAL_FIELDS = (
    "Word",
    "PartOfSpeech",
    "Definition",
    "Synonyms",
    "Examples",
)

PHRASAL_FRONT = (
    '{{#PartOfSpeech}}<div class="pos-line"><span class="badge">{{PartOfSpeech}}</span></div>{{/PartOfSpeech}}\n'
    '<div class="definition-prompt">{{Definition}}</div>'
)

PHRASAL_BACK = (
    "{{FrontSide}}\n"
    '<hr class="divider" id="answer">\n'
    '<div class="section section-word">'
    '<span class="section-label">Phrasal verb</span>'
    '<div class="value">{{Word}}</div>'
    "</div>\n"
    '{{#Synonyms}}<div class="section">'
    '<span class="section-label">Synonyms</span>'
    "<div>{{Synonyms}}</div>"
    "</div>{{/Synonyms}}\n"
    '{{#Examples}}<div class="section">'
    '<span class="section-label">Examples</span>'
    "<div>{{Examples}}</div>"
    "</div>{{/Examples}}"
)

# --- Word form ---

WORD_FORM_NOTE_TYPE = "VIP Word Form"
WORD_FORM_FIELDS = (
    "FrontSummary",
    "RootWord",
    "RootType",
    "RootDefinition",
    "FamilyHtml",
)

WORD_FORM_FRONT = '<div class="prompt">{{FrontSummary}}</div>'

WORD_FORM_BACK = (
    "{{FrontSide}}\n"
    '<hr class="divider" id="answer">\n'
    '{{#FamilyHtml}}<div class="section">'
    '<span class="section-label">Related forms</span>'
    '<div class="family">{{FamilyHtml}}</div>'
    "</div>{{/FamilyHtml}}\n"
    '<div class="section section-word">'
    '<span class="section-label">Root</span>'
    '<div class="value">{{RootWord}} <span class="badge">{{RootType}}</span></div>'
    "</div>\n"
    '{{#RootDefinition}}<div class="section">'
    '<span class="section-label">Root definition</span>'
    "<div>{{RootDefinition}}</div>"
    "</div>{{/RootDefinition}}"
)

# --- Word pattern ---

WORD_PATTERN_NOTE_TYPE = "VIP Word Pattern"
WORD_PATTERN_FIELDS = (
    "Gap",
    "Answer",
    "Pattern",
    "Explanation",
    "Examples",
)

WORD_PATTERN_FRONT = '<div class="gap-prompt">{{Gap}}</div>'

WORD_PATTERN_BACK = (
    "{{FrontSide}}\n"
    '<hr class="divider" id="answer">\n'
    '<div class="section section-answer">'
    '<span class="section-label">Answer</span>'
    '<div class="value">{{Answer}}</div>'
    "</div>\n"
    '{{#Pattern}}<div class="section">'
    '<span class="section-label">Pattern</span>'
    "<div>{{Pattern}}</div>"
    "</div>{{/Pattern}}\n"
    '{{#Explanation}}<div class="section">'
    '<span class="section-label">Explanation</span>'
    "<div>{{Explanation}}</div>"
    "</div>{{/Explanation}}\n"
    '{{#Examples}}<div class="section">'
    '<span class="section-label">Examples</span>'
    "<div>{{Examples}}</div>"
    "</div>{{/Examples}}"
)

_POS_ABBREV = {
    "noun": "N",
    "verb": "V",
    "adjective": "adj",
    "adverb": "adv",
    "preposition": "prep",
    "conjunction": "conj",
    "interjection": "interj",
    "pronoun": "pron",
    "determiner": "det",
    "phrasal verb": "phr.v",
}


def _join(values: Any) -> str:
    if not values:
        return ""
    if isinstance(values, str):
        return values
    return ", ".join(str(v) for v in values if v)


def _examples_html(values: Any) -> str:
    if not values:
        return ""
    if isinstance(values, str):
        items = [values] if values.strip() else []
    else:
        items = [str(v) for v in values if v]
    if not items:
        return ""
    lis = "".join(f"<li>{item}</li>" for item in items)
    return f'<ul class="examples-list">{lis}</ul>'


def _pos_abbrev(pos: str) -> str:
    cleaned = (pos or "").strip()
    if not cleaned:
        return "?"
    return _POS_ABBREV.get(cleaned.lower(), cleaned)


def _ensure_note_type(
    col: Collection,
    name: str,
    fields: tuple[str, ...],
    front: str,
    back: str,
) -> NotetypeDict:
    model = col.models.by_name(name)
    if model is None:
        model = col.models.new(name)
        for field_name in fields:
            col.models.add_field(model, col.models.new_field(field_name))
        template = col.models.new_template("Card 1")
        template["qfmt"] = front
        template["afmt"] = back
        col.models.add_template(model, template)
        model["css"] = CARD_CSS
        col.models.add(model)
        return model

    existing_names = {field["name"] for field in model["flds"]}
    for field_name in fields:
        if field_name not in existing_names:
            col.models.add_field(model, col.models.new_field(field_name))
    if model["tmpls"]:
        model["tmpls"][0]["qfmt"] = front
        model["tmpls"][0]["afmt"] = back
    model["css"] = CARD_CSS
    col.models.update_dict(model)
    return model


def ensure_note_type(col: Collection) -> NotetypeDict:
    return _ensure_note_type(col, NOTE_TYPE_NAME, FIELDS, CARD_FRONT, CARD_BACK)


def ensure_phrasal_note_type(col: Collection) -> NotetypeDict:
    return _ensure_note_type(
        col, PHRASAL_NOTE_TYPE, PHRASAL_FIELDS, PHRASAL_FRONT, PHRASAL_BACK
    )


def ensure_word_form_note_type(col: Collection) -> NotetypeDict:
    return _ensure_note_type(
        col,
        WORD_FORM_NOTE_TYPE,
        WORD_FORM_FIELDS,
        WORD_FORM_FRONT,
        WORD_FORM_BACK,
    )


def ensure_word_pattern_note_type(col: Collection) -> NotetypeDict:
    return _ensure_note_type(
        col,
        WORD_PATTERN_NOTE_TYPE,
        WORD_PATTERN_FIELDS,
        WORD_PATTERN_FRONT,
        WORD_PATTERN_BACK,
    )


def ensure_all_note_types(col: Collection) -> None:
    ensure_note_type(col)
    ensure_phrasal_note_type(col)
    ensure_word_form_note_type(col)
    ensure_word_pattern_note_type(col)


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
    note["Examples"] = _examples_html(result.get("examples"))
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


def add_phrasal_notes(
    col: Collection,
    deck_id: int,
    word: str,
    results: list[dict[str, Any]],
) -> int:
    model = ensure_phrasal_note_type(col)
    added = 0
    for result in results:
        note = col.new_note(model)
        note["Word"] = word
        note["PartOfSpeech"] = str(result.get("partOfSpeech") or "")
        note["Definition"] = str(result.get("definition") or "")
        note["Synonyms"] = _join(result.get("synonyms"))
        note["Examples"] = _examples_html(result.get("examples"))
        col.add_note(note, deck_id)
        added += 1
    return added


def _format_pos_count(count: int, abbrev: str) -> str:
    # e.g. 2N, 1 adj — space before multi-character abbreviations
    if len(abbrev) <= 1:
        return f"{count}{abbrev}"
    return f"{count} {abbrev}"


def _group_others_by_type(
    others: list[Any],
) -> list[tuple[str, list[dict[str, Any]]]]:
    """Group related forms by POS type, preserving first-seen type order."""
    groups: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for item in others:
        if not isinstance(item, dict):
            continue
        type_key = str(item.get("type") or "").strip().lower() or "?"
        if type_key not in groups:
            order.append(type_key)
            groups[type_key] = []
        groups[type_key].append(item)
    return [(key, groups[key]) for key in order]


def word_form_front_summary(payload: dict[str, Any]) -> str:
    """Preview of all selected types: able (adj), 2N, 1V."""
    root = payload.get("rootWord") or {}
    root_word = str(root.get("word") or "")
    root_type = _pos_abbrev(str(root.get("type") or ""))
    parts = [f"{root_word} ({root_type})"]
    for _key, items in _group_others_by_type(list(payload.get("other") or [])):
        abbrev = _pos_abbrev(str(items[0].get("type") or ""))
        parts.append(_format_pos_count(len(items), abbrev))
    return ", ".join(parts)


def word_form_card_summaries(payload: dict[str, Any]) -> list[str]:
    """One front line per type card that will be created."""
    root = payload.get("rootWord") or {}
    root_word = str(root.get("word") or "")
    root_type = _pos_abbrev(str(root.get("type") or ""))
    root_label = f"{root_word} ({root_type})"
    summaries: list[str] = []
    for _key, items in _group_others_by_type(list(payload.get("other") or [])):
        abbrev = _pos_abbrev(str(items[0].get("type") or ""))
        summaries.append(
            f"{root_label}, {_format_pos_count(len(items), abbrev)}"
        )
    return summaries


def word_form_front_html(root_word: str, root_type: str, count_label: str) -> str:
    root_abbrev = _pos_abbrev(root_type)
    return (
        f'<div class="prompt-root">{root_word}'
        f'<span class="badge">{root_abbrev}</span></div>'
        f'<div class="prompt-target">{count_label}</div>'
    )


def word_form_family_html(others: list[Any]) -> str:
    lines: list[str] = []
    for item in others:
        if not isinstance(item, dict):
            continue
        word = str(item.get("word") or "")
        pos = str(item.get("type") or "")
        special = item.get("special_definition")
        block = (
            '<div class="family-item">'
            f'<div class="family-word">{word}'
            f'<span class="badge">{pos}</span></div>'
        )
        if special:
            block += f'<div class="family-special">{special}</div>'
        block += "</div>"
        lines.append(block)
    return "\n".join(lines)


def add_word_form_notes(
    col: Collection,
    deck_id: int,
    payload: dict[str, Any],
) -> int:
    """Create one card per related-form POS type (e.g. nouns card, verbs card)."""
    model = ensure_word_form_note_type(col)
    root = payload.get("rootWord") or {}
    root_word = str(root.get("word") or "")
    root_type = str(root.get("type") or "")
    root_definition = str(root.get("definition") or "")

    groups = _group_others_by_type(list(payload.get("other") or []))
    added = 0
    for _key, items in groups:
        abbrev = _pos_abbrev(str(items[0].get("type") or ""))
        count_label = _format_pos_count(len(items), abbrev)
        note = col.new_note(model)
        note["FrontSummary"] = word_form_front_html(
            root_word, root_type, count_label
        )
        note["RootWord"] = root_word
        note["RootType"] = root_type
        note["RootDefinition"] = root_definition
        note["FamilyHtml"] = word_form_family_html(items)
        col.add_note(note, deck_id)
        added += 1
    return added


def add_word_pattern_note(
    col: Collection,
    deck_id: int,
    payload: dict[str, Any],
) -> int:
    model = ensure_word_pattern_note_type(col)
    note = col.new_note(model)
    note["Gap"] = str(payload.get("gap") or "")
    note["Answer"] = str(payload.get("answer") or "")
    note["Pattern"] = str(payload.get("pattern") or "")
    note["Explanation"] = str(payload.get("explanation") or "")
    note["Examples"] = _examples_html(payload.get("examples"))
    col.add_note(note, deck_id)
    return 1
