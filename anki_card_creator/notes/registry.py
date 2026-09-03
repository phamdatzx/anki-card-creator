from __future__ import annotations

from typing import Any

from .normal import (
    CARD_BACK as NORMAL_BACK,
)
from .normal import (
    CARD_FRONT as NORMAL_FRONT,
)
from .normal import (
    FIELDS as NORMAL_FIELDS,
)
from .normal import (
    NOTE_TYPE_NAME as NORMAL_NAME,
)
from .sentence import (
    CARD_BACK as SENTENCE_BACK,
)
from .sentence import (
    CARD_FRONT as SENTENCE_FRONT,
)
from .sentence import (
    FIELDS as SENTENCE_FIELDS,
)
from .sentence import (
    NOTE_TYPE_NAME as SENTENCE_NAME,
)
from .shared import CARD_CSS
from .word_form import (
    CARD_BACK as WORD_FORM_BACK,
)
from .word_form import (
    CARD_FRONT as WORD_FORM_FRONT,
)
from .word_form import (
    FIELDS as WORD_FORM_FIELDS,
)
from .word_form import (
    NOTE_TYPE_NAME as WORD_FORM_NAME,
)
from .word_pattern import (
    CARD_BACK as WORD_PATTERN_BACK,
)
from .word_pattern import (
    CARD_FRONT as WORD_PATTERN_FRONT,
)
from .word_pattern import (
    FIELDS as WORD_PATTERN_FIELDS,
)
from .word_pattern import (
    NOTE_TYPE_NAME as WORD_PATTERN_NAME,
)


def ensure_note_type(
    col: Any,
    name: str,
    fields: tuple[str, ...],
    front: str,
    back: str,
) -> Any:
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


def ensure_all_note_types(col: Any) -> None:
    ensure_note_type(col, NORMAL_NAME, NORMAL_FIELDS, NORMAL_FRONT, NORMAL_BACK)
    ensure_note_type(
        col, SENTENCE_NAME, SENTENCE_FIELDS, SENTENCE_FRONT, SENTENCE_BACK
    )
    ensure_note_type(
        col, WORD_FORM_NAME, WORD_FORM_FIELDS, WORD_FORM_FRONT, WORD_FORM_BACK
    )
    ensure_note_type(
        col,
        WORD_PATTERN_NAME,
        WORD_PATTERN_FIELDS,
        WORD_PATTERN_FRONT,
        WORD_PATTERN_BACK,
    )
