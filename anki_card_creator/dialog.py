from __future__ import annotations

from enum import Enum
from typing import Any

from aqt import mw
from aqt.addons import without_qt5_compat_wrapper
from aqt.qt import (
    QApplication,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QKeySequence,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QShortcut,
    QSize,
    Qt,
    ijkljj:without_qt5_compat_wrapperckedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import qconnect, showWarning, tooltip

from .api import WordsApiError, fetch_word
from .cards import (
    add_definition_notes,
    add_phrasal_notes,
    add_word_form_notes,
    add_word_pattern_note,
    ensure_all_note_types,
    word_form_card_summaries,
)
from .llm import LlmError
from .prompts import (
    lookup_normal_word,
    lookup_phrasal_verb,
    lookup_word_form,
    lookup_word_pattern,
)


class CardType(Enum):
    NORMAL = "normal"
    PHRASAL = "phrasal"
    WORD_FORM = "word_form"
    WORD_PATTERN = "word_pattern"


class NormalSource(Enum):
    WORDSAPI = "wordsapi"
    LLM = "llm"


def _addon_config() -> dict[str, Any]:
    addon = mw.addonManager.addonFromModule(__name__)
    return mw.addonManager.getConfig(addon) or {}


def _as_text(values: Any, *, multiline: bool = False) -> str:
    if not values:
        return ""
    if isinstance(values, str):
        return values
    sep = "\n" if multiline else ", "
    return sep.join(str(v) for v in values if v)


def _split_list(text: str, *, multiline: bool = False) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    if multiline and "\n" in cleaned:
        parts = cleaned.splitlines()
    else:
        parts = cleaned.split(",")
    return [part.strip() for part in parts if part.strip()]


def _parse_score(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _scores_compact(data: dict[str, Any] | None) -> str:
    """Short label for list rows, e.g. pop 4/5 · hard 2/5."""
    if not data:
        return ""
    pop_n = _parse_score(data.get("popularity"))
    diff_n = _parse_score(data.get("difficulty"))
    parts: list[str] = []
    if pop_n is not None:
        parts.append(f"pop {pop_n}/5")
    if diff_n is not None:
        parts.append(f"hard {diff_n}/5")
    return " · ".join(parts)


def _score_field_text(value: Any) -> str:
    parsed = _parse_score(value)
    return "" if parsed is None else str(parsed)


def _read_score_field(text: str) -> int | None:
    return _parse_score(text.strip())


def _item_label(result: dict[str, Any]) -> str:
    pos = result.get("partOfSpeech") or "?"
    definition = result.get("definition") or ""
    scores = _scores_compact(result)
    body = f"[{pos}] {definition}"
    if scores:
        return f"{scores}\n{body}"
    return body


def _family_item_label(item: dict[str, Any]) -> str:
    word = item.get("word") or "?"
    pos = item.get("type") or "?"
    special = item.get("special_definition")
    scores = _scores_compact(item)
    if special:
        body = f"{word} ({pos}) — {special}"
    else:
        body = f"{word} ({pos})"
    if scores:
        return f"{scores}\n{body}"
    return body


def _fit_list_item(list_widget: QListWidget, item: QListWidgetItem) -> None:
    """Size the row so wrapped text is fully visible (no horizontal scroll)."""
    width = max(list_widget.viewport().width() - 28, 80)
    metrics = list_widget.fontMetrics()
    bounds = metrics.boundingRect(
        0,
        0,
        width,
        10_000,
        Qt.TextFlag.TextWordWrap | Qt.TextFlag.TextExpandTabs,
        item.text(),
    )
    item.setSizeHint(QSize(width, bounds.height() + 10))


def _refit_list(list_widget: QListWidget) -> None:
    for index in range(list_widget.count()):
        item = list_widget.item(index)
        if item is not None:
            _fit_list_item(list_widget, item)


def _current_deck_id() -> int:
    try:
        return int(mw.col.decks.get_current_id())
    except AttributeError:
        return int(mw.col.decks.current()["id"])


def _openai_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "api_key": str(config.get("openai_api_key") or ""),
        "model": str(config.get("openai_model") or "gpt-5-mini"),
        "base_url": str(
            config.get("openai_base_url") or "https://api.openai.com/v1"
        ),
        "verify_ssl": bool(config.get("verify_ssl", False)),
    }


class DefinitionDetailDialog(QDialog):
    def __init__(self, result: dict[str, Any], word: str = "", parent=None) -> None:
        super().__init__(parent or mw)
        title = f"Edit definition — {word}" if word else "Edit definition"
        self.setWindowTitle(title)
        self.resize(480, 400)
        self._original = dict(result)

        self._definition = QTextEdit()
        self._definition.setPlainText(str(result.get("definition") or ""))
        self._definition.setMinimumHeight(80)

        self._pos = QLineEdit(str(result.get("partOfSpeech") or ""))

        self._synonyms = QLineEdit(_as_text(result.get("synonyms")))
        self._synonyms.setPlaceholderText("comma-separated")

        self._examples = QTextEdit()
        self._examples.setPlainText(_as_text(result.get("examples"), multiline=True))
        self._examples.setPlaceholderText("one example per line, or comma-separated")
        self._examples.setMinimumHeight(80)

        self._popularity = QLineEdit(_score_field_text(result.get("popularity")))
        self._popularity.setPlaceholderText("1–5")
        self._difficulty = QLineEdit(_score_field_text(result.get("difficulty")))
        self._difficulty.setPlaceholderText("1–5")

        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.addRow("Definition:", self._definition)
        form.addRow("Part of speech:", self._pos)
        form.addRow("Synonyms:", self._synonyms)
        form.addRow("Examples:", self._examples)
        form.addRow("Popularity (1–5):", self._popularity)
        form.addRow("Difficulty (1–5):", self._difficulty)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        qconnect(buttons.accepted, self.accept)
        qconnect(buttons.rejected, self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def result_data(self) -> dict[str, Any]:
        data = dict(self._original)
        data["definition"] = self._definition.toPlainText().strip()
        data["partOfSpeech"] = self._pos.text().strip()
        data["synonyms"] = _split_list(self._synonyms.text())
        data["examples"] = _split_list(
            self._examples.toPlainText(), multiline=True
        )
        data["popularity"] = _read_score_field(self._popularity.text())
        data["difficulty"] = _read_score_field(self._difficulty.text())
        return data


class FamilyMemberDialog(QDialog):
    def __init__(self, item: dict[str, Any], parent=None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("Edit word form")
        self.resize(420, 280)
        self._original = dict(item)

        self._word = QLineEdit(str(item.get("word") or ""))
        self._type = QLineEdit(str(item.get("type") or ""))
        special = item.get("special_definition")
        self._special = QTextEdit()
        self._special.setPlainText("" if special is None else str(special))
        self._special.setPlaceholderText(
            "Only if meaning differs a lot from the root; leave empty otherwise"
        )
        self._special.setMinimumHeight(80)
        self._popularity = QLineEdit(_score_field_text(item.get("popularity")))
        self._popularity.setPlaceholderText("1–5")
        self._difficulty = QLineEdit(_score_field_text(item.get("difficulty")))
        self._difficulty.setPlaceholderText("1–5")

        form = QFormLayout()
        form.addRow("Word:", self._word)
        form.addRow("Type:", self._type)
        form.addRow("Special definition:", self._special)
        form.addRow("Popularity (1–5):", self._popularity)
        form.addRow("Difficulty (1–5):", self._difficulty)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        qconnect(buttons.accepted, self.accept)
        qconnect(buttons.rejected, self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def result_data(self) -> dict[str, Any]:
        data = dict(self._original)
        data["word"] = self._word.text().strip()
        data["type"] = self._type.text().strip()
        special = self._special.toPlainText().strip()
        data["special_definition"] = special or None
        data["popularity"] = _read_score_field(self._popularity.text())
        data["difficulty"] = _read_score_field(self._difficulty.text())
        return data


def _pronunciation_text(payload: dict[str, Any]) -> str:
    pron = payload.get("pronunciation")
    if isinstance(pron, dict):
        return str(pron.get("all") or "")
    if isinstance(pron, str):
        return pron
    return ""


def _syllable_count_text(payload: dict[str, Any]) -> str:
    syllables = payload.get("syllables")
    if isinstance(syllables, dict) and syllables.get("count") is not None:
        return str(syllables["count"])
    return ""


class LookupDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("Anki Card Creator")
        self.resize(600, 560)

        self._payload: dict[str, Any] | None = None
        self._word_form_payload: dict[str, Any] | None = None
        self._word_pattern_payload: dict[str, Any] | None = None

        self._type_group = QButtonGroup(self)
        self._radio_normal = QRadioButton("Normal")
        self._radio_phrasal = QRadioButton("Phrasal verb")
        self._radio_form = QRadioButton("Word form")
        self._radio_pattern = QRadioButton("Word pattern")
        self._radio_normal.setChecked(True)
        for index, radio in enumerate(
            (
                self._radio_normal,
                self._radio_phrasal,
                self._radio_form,
                self._radio_pattern,
            )
        ):
            self._type_group.addButton(radio, index)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Card type:"))
        type_row.addWidget(self._radio_normal)
        type_row.addWidget(self._radio_phrasal)
        type_row.addWidget(self._radio_form)
        type_row.addWidget(self._radio_pattern)
        type_row.addStretch(1)

        self._source_group = QButtonGroup(self)
        self._radio_wordsapi = QRadioButton("WordsAPI")
        self._radio_llm = QRadioButton("LLM")
        self._radio_wordsapi.setChecked(True)
        self._source_group.addButton(self._radio_wordsapi, 0)
        self._source_group.addButton(self._radio_llm, 1)

        self._source_row = QWidget()
        source_layout = QHBoxLayout(self._source_row)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.addWidget(QLabel("Source:"))
        source_layout.addWidget(self._radio_wordsapi)
        source_layout.addWidget(self._radio_llm)
        source_layout.addStretch(1)

        self._input_stack = QStackedWidget()
        self._input_stack.addWidget(self._build_word_input("Enter a word…"))
        self._input_stack.addWidget(self._build_word_input("Enter a phrasal verb…"))
        self._input_stack.addWidget(self._build_word_input("Enter a word (any form)…"))
        self._input_stack.addWidget(
            self._build_word_input("Enter a pattern (e.g. make a decision)…")
        )

        self._status = QLabel("Choose a card type, enter input, then look it up.")
        self._status.setWordWrap(True)

        self._result_stack = QStackedWidget()
        self._def_list = QListWidget()
        self._def_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._def_list.setWordWrap(True)
        self._def_list.setTextElideMode(Qt.TextElideMode.ElideNone)
        self._def_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._result_stack.addWidget(self._def_list)

        self._form_panel = self._build_word_form_panel()
        self._result_stack.addWidget(self._form_panel)

        self._pattern_panel = self._build_pattern_panel()
        self._result_stack.addWidget(self._pattern_panel)

        self._create_btn = QPushButton("Create cards (Ctrl+Enter)")
        self._create_btn.setEnabled(False)
        self._create_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)

        layout = QVBoxLayout(self)
        layout.addLayout(type_row)
        layout.addWidget(self._source_row)
        layout.addWidget(self._input_stack)
        layout.addWidget(self._status)
        layout.addWidget(self._result_stack, stretch=1)
        layout.addWidget(self._create_btn)
        layout.addWidget(close_box)

        for radio in (
            self._radio_normal,
            self._radio_phrasal,
            self._radio_form,
            self._radio_pattern,
        ):
            qconnect(radio.toggled, self._on_type_toggled)
        for radio in (self._radio_wordsapi, self._radio_llm):
            qconnect(radio.toggled, self._on_source_toggled)
        qconnect(self._def_list.itemDoubleClicked, self._on_def_double_clicked)
        qconnect(self._family_list.itemDoubleClicked, self._on_family_double_clicked)
        qconnect(self._create_btn.clicked, self._on_create)
        qconnect(self._create_shortcut.activated, self._on_create)
        qconnect(close_box.rejected, self.reject)

        self._apply_type_ui()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        _refit_list(self._def_list)
        _refit_list(self._family_list)

    def _build_word_input(self, placeholder: str) -> QWidget:
        panel = QWidget()
        row = QHBoxLayout(panel)
        row.setContentsMargins(0, 0, 0, 0)
        line = QLineEdit()
        line.setPlaceholderText(placeholder)
        btn = QPushButton("Look up")
        row.addWidget(line, stretch=1)
        row.addWidget(btn)
        qconnect(btn.clicked, self._on_lookup)
        qconnect(line.returnPressed, self._on_lookup)
        panel._line = line  # noqa: SLF001 - panel-local handle
        panel._btn = btn  # noqa: SLF001
        return panel

    def _build_word_form_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self._form_summary = QLabel("")
        self._form_summary.setWordWrap(True)
        self._root_word = QLineEdit()
        self._root_type = QLineEdit()
        self._root_definition = QTextEdit()
        self._root_definition.setFixedHeight(40)
        self._root_definition.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._root_popularity = QLineEdit()
        self._root_popularity.setPlaceholderText("1–5")
        self._root_difficulty = QLineEdit()
        self._root_difficulty.setPlaceholderText("1–5")

        form = QFormLayout()
        form.addRow("Root word:", self._root_word)
        form.addRow("Root type:", self._root_type)
        form.addRow("Root definition:", self._root_definition)
        form.addRow("Root popularity:", self._root_popularity)
        form.addRow("Root difficulty:", self._root_difficulty)

        self._family_list = QListWidget()
        self._family_list.setMinimumHeight(220)
        self._family_list.setWordWrap(True)
        self._family_list.setTextElideMode(Qt.TextElideMode.ElideNone)
        self._family_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        family_label = QLabel(
            "Related forms (check to include; double-click to edit):"
        )

        layout.addWidget(self._form_summary)
        layout.addLayout(form)
        layout.addWidget(family_label)
        layout.addWidget(self._family_list, stretch=1)

        qconnect(self._root_word.textChanged, lambda _t: self._refresh_form_summary())
        qconnect(self._root_type.textChanged, lambda _t: self._refresh_form_summary())
        qconnect(self._family_list.itemChanged, self._on_family_item_changed)
        return panel

    def _build_pattern_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self._pattern_gap = QLineEdit()
        self._pattern_answer = QLineEdit()
        self._pattern_full = QLineEdit()
        self._pattern_explanation = QTextEdit()
        self._pattern_explanation.setMinimumHeight(60)
        self._pattern_examples = QTextEdit()
        self._pattern_examples.setPlaceholderText("one example per line")
        self._pattern_examples.setMinimumHeight(80)

        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.addRow("Gap (front):", self._pattern_gap)
        form.addRow("Answer:", self._pattern_answer)
        form.addRow("Pattern:", self._pattern_full)
        form.addRow("Explanation:", self._pattern_explanation)
        form.addRow("Examples:", self._pattern_examples)
        layout.addLayout(form)
        layout.addStretch(1)
        return panel

    def _card_type(self) -> CardType:
        checked = self._type_group.checkedId()
        return (
            CardType.NORMAL,
            CardType.PHRASAL,
            CardType.WORD_FORM,
            CardType.WORD_PATTERN,
        )[checked]

    def _normal_source(self) -> NormalSource:
        if self._radio_llm.isChecked():
            return NormalSource.LLM
        return NormalSource.WORDSAPI

    def _active_input(self) -> tuple[QLineEdit, QPushButton]:
        panel = self._input_stack.currentWidget()
        return panel._line, panel._btn  # noqa: SLF001

    def _set_busy(self, busy: bool) -> None:
        enabled = not busy
        for index in range(self._input_stack.count()):
            panel = self._input_stack.widget(index)
            panel._btn.setEnabled(enabled)  # noqa: SLF001
            panel._line.setEnabled(enabled)  # noqa: SLF001
        for radio in (
            self._radio_normal,
            self._radio_phrasal,
            self._radio_form,
            self._radio_pattern,
            self._radio_wordsapi,
            self._radio_llm,
        ):
            radio.setEnabled(enabled)
        # Keep create enabled only when not busy and results already allow it.
        if busy:
            self._create_btn.setEnabled(False)
        else:
            self._create_btn.setEnabled(self._can_create())

    def _can_create(self) -> bool:
        card_type = self._card_type()
        if card_type in (CardType.NORMAL, CardType.PHRASAL):
            return self._payload is not None and self._def_list.count() > 0
        if card_type is CardType.WORD_FORM:
            return self._word_form_payload is not None
        return self._word_pattern_payload is not None

    def _clear_results(self) -> None:
        self._payload = None
        self._word_form_payload = None
        self._word_pattern_payload = None
        self._def_list.clear()
        self._family_list.clear()
        self._form_summary.setText("")
        self._root_word.clear()
        self._root_type.clear()
        self._root_definition.clear()
        self._root_popularity.clear()
        self._root_difficulty.clear()
        self._pattern_gap.clear()
        self._pattern_answer.clear()
        self._pattern_full.clear()
        self._pattern_explanation.clear()
        self._pattern_examples.clear()
        self._create_btn.setEnabled(False)

    def _ready_hint(self) -> str:
        hints = {
            CardType.NORMAL: self._normal_hint(),
            CardType.PHRASAL: "Phrasal verb: OpenAI senses — pick definitions to card.",
            CardType.WORD_FORM: "Word form: OpenAI finds the true root + related forms — one card per type.",
            CardType.WORD_PATTERN: "Word pattern: OpenAI gap fill — edit, then create one card.",
        }
        return hints[self._card_type()]

    def _reset_after_create(self, added: int) -> None:
        self._clear_results()
        line, _ = self._active_input()
        line.clear()
        line.setFocus()
        self._status.setText(
            f"Created {added} card(s) in the current deck. {self._ready_hint()}"
        )

    def _on_type_toggled(self, checked: bool) -> None:
        if checked:
            self._apply_type_ui()

    def _on_source_toggled(self, checked: bool) -> None:
        if checked and self._card_type() is CardType.NORMAL:
            self._clear_results()
            self._status.setText(self._normal_hint())

    def _normal_hint(self) -> str:
        if self._normal_source() is NormalSource.LLM:
            return "Normal (LLM): OpenAI senses — pick definitions to card."
        return "Normal (WordsAPI): pick definitions to card."

    def _apply_type_ui(self) -> None:
        card_type = self._card_type()
        type_index = {
            CardType.NORMAL: 0,
            CardType.PHRASAL: 1,
            CardType.WORD_FORM: 2,
            CardType.WORD_PATTERN: 3,
        }[card_type]
        self._input_stack.setCurrentIndex(type_index)
        self._source_row.setVisible(card_type is CardType.NORMAL)

        if card_type in (CardType.NORMAL, CardType.PHRASAL):
            self._result_stack.setCurrentIndex(0)
        elif card_type is CardType.WORD_FORM:
            self._result_stack.setCurrentIndex(1)
        else:
            self._result_stack.setCurrentIndex(2)

        self._clear_results()
        self._status.setText(self._ready_hint())

    def _on_def_double_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data, dict):
            return
        word = ""
        if self._payload:
            word = str(self._payload.get("word") or "")
        dialog = DefinitionDetailDialog(data, word=word, parent=self)
        if dialog.exec():
            edited = dialog.result_data()
            item.setData(Qt.ItemDataRole.UserRole, edited)
            item.setText(_item_label(edited))
            _fit_list_item(self._def_list, item)

    def _on_family_double_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data, dict):
            return
        dialog = FamilyMemberDialog(data, parent=self)
        if dialog.exec():
            edited = dialog.result_data()
            item.setData(Qt.ItemDataRole.UserRole, edited)
            item.setText(_family_item_label(edited))
            _fit_list_item(self._family_list, item)
            self._refresh_form_summary()

    def _on_family_item_changed(self, _item: QListWidgetItem) -> None:
        self._refresh_form_summary()

    def _refresh_form_summary(self) -> None:
        payload = self._collect_word_form_payload(selected_only=True)
        cards = word_form_card_summaries(payload)
        if not cards:
            self._form_summary.setText("Check at least one related form to create cards.")
            return
        self._form_summary.setText(
            f"Will create {len(cards)} card(s):\n" + "\n".join(f"• {s}" for s in cards)
        )

    def _fill_definition_list(self, payload: dict[str, Any], word: str) -> None:
        results = payload.get("results") or []
        if not results:
            self._status.setText(f'No definitions for "{word}".')
            return

        self._payload = payload
        for result in results:
            item = QListWidgetItem(_item_label(result))
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
            )
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, dict(result))
            self._def_list.addItem(item)
            _fit_list_item(self._def_list, item)

        self._status.setText(
            f'{payload.get("word", word)} — double-click to edit; '
            "check definitions, then create cards."
        )
        self._create_btn.setEnabled(True)

    def _fill_word_form(self, payload: dict[str, Any]) -> None:
        self._word_form_payload = payload
        root = payload.get("rootWord") or {}
        self._root_word.setText(str(root.get("word") or ""))
        self._root_type.setText(str(root.get("type") or ""))
        self._root_definition.setPlainText(str(root.get("definition") or ""))
        self._root_popularity.setText(_score_field_text(root.get("popularity")))
        self._root_difficulty.setText(_score_field_text(root.get("difficulty")))
        self._family_list.blockSignals(True)
        self._family_list.clear()
        for item_data in payload.get("other") or []:
            if not isinstance(item_data, dict):
                continue
            item = QListWidgetItem(_family_item_label(item_data))
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
            )
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, dict(item_data))
            self._family_list.addItem(item)
            _fit_list_item(self._family_list, item)
        self._family_list.blockSignals(False)
        self._refresh_form_summary()
        self._status.setText(
            "Check related forms; one card is created per type (e.g. nouns, verbs)."
        )
        self._create_btn.setEnabled(True)

    def _fill_word_pattern(self, payload: dict[str, Any]) -> None:
        self._word_pattern_payload = payload
        self._pattern_gap.setText(str(payload.get("gap") or ""))
        self._pattern_answer.setText(str(payload.get("answer") or ""))
        self._pattern_full.setText(str(payload.get("pattern") or ""))
        self._pattern_explanation.setPlainText(str(payload.get("explanation") or ""))
        self._pattern_examples.setPlainText(
            _as_text(payload.get("examples"), multiline=True)
        )
        self._status.setText("Edit the gap card if needed, then create.")
        self._create_btn.setEnabled(True)

    def _on_lookup(self) -> None:
        card_type = self._card_type()
        line, _btn = self._active_input()
        text = line.text().strip()
        config = _addon_config()

        self._clear_results()
        self._status.setText("Looking up…")
        self._set_busy(True)
        QApplication.processEvents()

        try:
            if card_type is CardType.NORMAL:
                if self._normal_source() is NormalSource.LLM:
                    payload = lookup_normal_word(text, **_openai_kwargs(config))
                    self._fill_definition_list(payload, text)
                else:
                    payload = fetch_word(
                        text,
                        api_key=str(config.get("rapidapi_key") or ""),
                        host=str(
                            config.get("rapidapi_host")
                            or "wordsapiv1.p.rapidapi.com"
                        ),
                        verify_ssl=bool(config.get("verify_ssl", False)),
                    )
                    pronunciation = _pronunciation_text(payload)
                    syllable_count = _syllable_count_text(payload)
                    suffix_parts = []
                    if pronunciation:
                        suffix_parts.append(pronunciation)
                    if syllable_count:
                        suffix_parts.append(f"{syllable_count} syllables")
                    self._fill_definition_list(payload, text)
                    if self._payload and suffix_parts:
                        self._status.setText(
                            f'{payload.get("word", text)} · '
                            f'{" · ".join(suffix_parts)}'
                            " — double-click to edit; check definitions, "
                            "then create cards."
                        )
            elif card_type is CardType.PHRASAL:
                payload = lookup_phrasal_verb(text, **_openai_kwargs(config))
                self._fill_definition_list(payload, text)
            elif card_type is CardType.WORD_FORM:
                payload = lookup_word_form(text, **_openai_kwargs(config))
                self._fill_word_form(payload)
            else:
                payload = lookup_word_pattern(text, **_openai_kwargs(config))
                self._fill_word_pattern(payload)
        except (WordsApiError, LlmError) as exc:
            self._status.setText(str(exc))
            showWarning(str(exc), parent=self)
        finally:
            self._set_busy(False)

    def _selected_results(self) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        for index in range(self._def_list.count()):
            item = self._def_list.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, dict):
                    selected.append(data)
        return selected

    def _collect_word_form_payload(
        self, *, selected_only: bool = True
    ) -> dict[str, Any]:
        others: list[dict[str, Any]] = []
        for index in range(self._family_list.count()):
            item = self._family_list.item(index)
            if selected_only and item.checkState() != Qt.CheckState.Checked:
                continue
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, dict):
                others.append(data)
        return {
            "rootWord": {
                "word": self._root_word.text().strip(),
                "type": self._root_type.text().strip(),
                "definition": self._root_definition.toPlainText().strip(),
                "popularity": _read_score_field(self._root_popularity.text()),
                "difficulty": _read_score_field(self._root_difficulty.text()),
            },
            "other": others,
        }

    def _collect_word_pattern_payload(self) -> dict[str, Any]:
        return {
            "gap": self._pattern_gap.text().strip(),
            "answer": self._pattern_answer.text().strip(),
            "pattern": self._pattern_full.text().strip(),
            "explanation": self._pattern_explanation.toPlainText().strip(),
            "examples": _split_list(
                self._pattern_examples.toPlainText(), multiline=True
            ),
        }

    def _on_create(self) -> None:
        card_type = self._card_type()
        deck_id = _current_deck_id()

        # Validate before showing waiting UI.
        if card_type is CardType.NORMAL:
            if not self._payload:
                showWarning("Look up a word first.", parent=self)
                return
            selected = self._selected_results()
            if not selected:
                showWarning("Select at least one definition.", parent=self)
                return
        elif card_type is CardType.PHRASAL:
            if not self._payload:
                showWarning("Look up a phrasal verb first.", parent=self)
                return
            selected = self._selected_results()
            if not selected:
                showWarning("Select at least one definition.", parent=self)
                return
        elif card_type is CardType.WORD_FORM:
            if self._word_form_payload is None:
                showWarning("Look up a word form first.", parent=self)
                return
            payload = self._collect_word_form_payload()
            if not payload["rootWord"]["word"]:
                showWarning("Root word is required.", parent=self)
                return
            if not payload["other"]:
                showWarning(
                    "Select at least one related form (checkbox).",
                    parent=self,
                )
                return
        else:
            if self._word_pattern_payload is None:
                showWarning("Look up a pattern first.", parent=self)
                return
            payload = self._collect_word_pattern_payload()
            if not payload["gap"] or not payload["answer"]:
                showWarning("Gap and answer are required.", parent=self)
                return

        self._status.setText("Creating cards…")
        self._set_busy(True)
        QApplication.processEvents()

        try:
            if card_type is CardType.NORMAL:
                line, _ = self._active_input()
                word = str(self._payload.get("word") or line.text().strip())
                added = add_definition_notes(
                    mw.col,
                    deck_id,
                    word,
                    _pronunciation_text(self._payload),
                    _syllable_count_text(self._payload),
                    selected,
                )
            elif card_type is CardType.PHRASAL:
                line, _ = self._active_input()
                word = str(self._payload.get("word") or line.text().strip())
                added = add_phrasal_notes(mw.col, deck_id, word, selected)
            elif card_type is CardType.WORD_FORM:
                added = add_word_form_notes(mw.col, deck_id, payload)
            else:
                added = add_word_pattern_note(mw.col, deck_id, payload)
        except Exception as exc:  # noqa: BLE001 - show to user
            self._status.setText(f"Could not create cards: {exc}")
            showWarning(f"Could not create cards: {exc}", parent=self)
            self._set_busy(False)
            return

        mw.reset()
        tooltip(f"Added {added} card(s) to the current deck.", parent=mw)
        self._set_busy(False)
        self._reset_after_create(added)


def open_lookup_dialog() -> None:
    if mw.col is None:
        showWarning("Open a profile / collection first.")
        return
    ensure_all_note_types(mw.col)
    dialog = LookupDialog(mw)
    dialog.exec()
