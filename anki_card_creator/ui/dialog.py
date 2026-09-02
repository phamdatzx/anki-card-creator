from __future__ import annotations

from enum import Enum
from typing import cast

from aqt import mw
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
    QStackedWidget,
    Qt,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import qconnect, showWarning, tooltip

from ..audio import definition_audio_tags, word_form_audio
from ..config import AddonConfig, chat_kwargs, normalize_config
from ..lookups.contracts import (
    DefinitionResult,
    NormalPayload,
    WordFormItem,
    WordFormPayload,
    WordPatternPayload,
)
from ..lookups.normal import lookup_normal_word
from ..lookups.word_form import lookup_word_form
from ..lookups.word_pattern import lookup_word_pattern
from ..notes.normal import add_definition_notes
from ..notes.registry import ensure_all_note_types
from ..notes.word_form import add_word_form_notes, word_form_card_summaries
from ..notes.word_pattern import add_word_pattern_note
from ..openai_client import OpenAIError
from ..text import as_text, parse_score, score_field_text, split_list
from .editors import DefinitionDetailDialog, FamilyMemberDialog
from .formatting import (
    family_item_label,
    item_label,
)
from .widgets import CheckToggleListWidget, InputPanel, fit_list_item, refit_list


class CardType(Enum):
    NORMAL = 0
    WORD_FORM = 1
    WORD_PATTERN = 2


def addon_config() -> AddonConfig:
    addon = mw.addonManager.addonFromModule(__name__)
    return normalize_config(mw.addonManager.getConfig(addon))


def current_deck_id() -> int:
    try:
        return int(mw.col.decks.get_current_id())
    except AttributeError:
        return int(mw.col.decks.current()["id"])


class LookupDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("Anki Card Creator")
        self.resize(600, 560)
        self._normal_payload: NormalPayload | None = None
        self._form_payload: WordFormPayload | None = None
        self._pattern_payload: WordPatternPayload | None = None

        self._type_group = QButtonGroup(self)
        radios = [
            QRadioButton("Normal"),
            QRadioButton("Word form"),
            QRadioButton("Word pattern"),
        ]
        self._radios = radios
        radios[0].setChecked(True)
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Card type:"))
        for index, radio in enumerate(radios):
            self._type_group.addButton(radio, index)
            type_row.addWidget(radio)
            qconnect(radio.toggled, self._type_changed)
        type_row.addStretch()

        self._inputs = QStackedWidget()
        for placeholder in (
            "Enter a word or phrasal verb…",
            "Enter a word (any form)…",
            "Enter a pattern (e.g. make a decision)…",
        ):
            self._inputs.addWidget(InputPanel(placeholder, self._lookup))
        self._status = QLabel("")
        self._status.setWordWrap(True)
        self._results = QStackedWidget()
        self._definitions = CheckToggleListWidget()
        self._setup_list(self._definitions)
        self._results.addWidget(self._definitions)
        self._results.addWidget(self._form_panel())
        self._results.addWidget(self._pattern_panel())
        self._create = QPushButton("Create cards (Ctrl+Enter)")
        self._create.setEnabled(False)
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)

        layout = QVBoxLayout(self)
        layout.addLayout(type_row)
        layout.addWidget(self._inputs)
        layout.addWidget(self._status)
        layout.addWidget(self._results, stretch=1)
        layout.addWidget(self._create)
        layout.addWidget(close_box)
        qconnect(self._definitions.itemDoubleClicked, self._edit_definition)
        qconnect(self._family.itemDoubleClicked, self._edit_family)
        qconnect(self._family.itemChanged, lambda _item: self._refresh_summary())
        qconnect(self._create.clicked, self._create_cards)
        qconnect(shortcut.activated, self._create_cards)
        qconnect(close_box.rejected, self.reject)
        self._apply_type()

    @staticmethod
    def _setup_list(widget: QListWidget) -> None:
        widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        widget.setWordWrap(True)
        widget.setTextElideMode(Qt.TextElideMode.ElideNone)
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)

    def _form_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        self._summary = QLabel("")
        self._summary.setWordWrap(True)
        self._root_word = QLineEdit()
        self._root_type = QLineEdit()
        self._root_ipa = QLineEdit()
        self._root_ipa.setPlaceholderText("/ˈwɜrd/")
        self._root_definition = QTextEdit()
        self._root_definition.setFixedHeight(40)
        self._root_definition.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._root_vietnamese = QLineEdit()
        self._root_popularity = QLineEdit()
        self._root_popularity.setPlaceholderText("1–5")
        self._root_difficulty = QLineEdit()
        self._root_difficulty.setPlaceholderText("1–5")
        form = QFormLayout()
        for label, widget in (
            ("Root word:", self._root_word),
            ("Root type:", self._root_type),
            ("Root IPA:", self._root_ipa),
            ("Root definition:", self._root_definition),
            ("Root Vietnamese:", self._root_vietnamese),
            ("Root popularity:", self._root_popularity),
            ("Root difficulty:", self._root_difficulty),
        ):
            form.addRow(label, widget)
        self._family = CheckToggleListWidget()
        self._setup_list(self._family)
        self._family.setMinimumHeight(220)
        self._family.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._summary)
        layout.addLayout(form)
        layout.addWidget(QLabel("Related forms (click to toggle; double-click to edit):"))
        layout.addWidget(self._family, stretch=1)
        qconnect(self._root_word.textChanged, lambda _text: self._refresh_summary())
        qconnect(self._root_type.textChanged, lambda _text: self._refresh_summary())
        return panel

    def _pattern_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self._gap = QTextEdit()
        self._gap.setMinimumHeight(110)
        self._gap.setAcceptRichText(False)
        self._gap.setPlaceholderText(
            "Gap sentence — e.g. She (đưa ra quyết định) to quit her job."
        )
        self._gap.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._vietnamese = QLineEdit()
        self._vietnamese.setPlaceholderText("Vietnamese meaning of the pattern")
        self._answer = QLineEdit()
        self._pattern = QLineEdit()
        self._explanation = QTextEdit()
        self._explanation.setMinimumHeight(60)
        self._examples = QTextEdit()
        self._examples.setPlaceholderText("one example per line")
        self._examples.setMinimumHeight(80)
        for label, widget in (
            ("Gap (front):", self._gap),
            ("Vietnamese:", self._vietnamese),
            ("Answer:", self._answer),
            ("Pattern:", self._pattern),
            ("Explanation:", self._explanation),
            ("Examples:", self._examples),
        ):
            form.addRow(label, widget)
        layout.addLayout(form)
        layout.addStretch(1)
        return panel

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        refit_list(self._definitions)
        refit_list(self._family)

    def _card_type(self) -> CardType:
        return CardType(self._type_group.checkedId())

    def _active_input(self) -> InputPanel:
        return cast(InputPanel, self._inputs.currentWidget())

    def _type_changed(self, checked: bool) -> None:
        if checked:
            self._apply_type()

    def _apply_type(self) -> None:
        index = self._card_type().value
        self._inputs.setCurrentIndex(index)
        self._results.setCurrentIndex(index)
        self._clear()
        hints = (
            "Normal: look up senses and select definitions.",
            "Word form: find a root and related forms.",
            "Word pattern: create a contextual gap fill.",
        )
        self._status.setText(hints[index])

    def _clear(self) -> None:
        self._normal_payload = self._form_payload = self._pattern_payload = None
        self._definitions.clear()
        self._family.clear()
        self._summary.clear()
        for widget in (
            self._root_word,
            self._root_type,
            self._root_ipa,
            self._root_vietnamese,
            self._root_popularity,
            self._root_difficulty,
            self._answer,
            self._pattern,
            self._vietnamese,
        ):
            widget.clear()
        for widget in (
            self._root_definition,
            self._gap,
            self._explanation,
            self._examples,
        ):
            widget.clear()
        self._create.setEnabled(False)

    def _busy(self, busy: bool) -> None:
        for index in range(self._inputs.count()):
            panel = cast(InputPanel, self._inputs.widget(index))
            panel.line.setEnabled(not busy)
            panel.button.setEnabled(not busy)
        for radio in self._radios:
            radio.setEnabled(not busy)
        self._create.setEnabled(not busy and self._can_create())

    def _can_create(self) -> bool:
        return (
            self._normal_payload is not None and self._definitions.count() > 0
            if self._card_type() is CardType.NORMAL
            else self._form_payload is not None
            if self._card_type() is CardType.WORD_FORM
            else self._pattern_payload is not None
        )

    def _lookup(self) -> None:
        panel = self._active_input()
        text = panel.line.text().strip()
        config = addon_config()
        self._clear()
        self._busy(True)
        self._status.setText("Looking up…")
        QApplication.processEvents()
        try:
            if self._card_type() is CardType.NORMAL:
                self._fill_normal(lookup_normal_word(text, **chat_kwargs(config)))
            elif self._card_type() is CardType.WORD_FORM:
                self._fill_form(lookup_word_form(text, **chat_kwargs(config)))
            else:
                self._fill_pattern(lookup_word_pattern(text, **chat_kwargs(config)))
        except OpenAIError as exc:
            self._status.setText(str(exc))
            showWarning(str(exc), parent=self)
        finally:
            self._busy(False)

    def _fill_normal(self, payload: NormalPayload) -> None:
        results = payload.get("results") or []
        if not results:
            self._status.setText(
                f'No definitions for "{payload.get("word") or ""}".'
            )
            return
        self._normal_payload = payload
        for result in results:
            item = QListWidgetItem(item_label(result))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, dict(result))
            self._definitions.addItem(item)
            fit_list_item(self._definitions, item)
        self._status.setText("Select definitions; double-click to edit.")

    def _fill_form(self, payload: WordFormPayload) -> None:
        self._form_payload = payload
        root = payload.get("rootWord") or {}
        self._root_word.setText(str(root.get("word") or ""))
        self._root_type.setText(str(root.get("type") or ""))
        self._root_ipa.setText(str(root.get("ipa") or ""))
        self._root_definition.setPlainText(str(root.get("definition") or ""))
        self._root_vietnamese.setText(str(root.get("vietnamese") or ""))
        self._root_popularity.setText(score_field_text(root.get("popularity")))
        self._root_difficulty.setText(score_field_text(root.get("difficulty")))
        self._family.blockSignals(True)
        for data in payload.get("other") or []:
            item = QListWidgetItem(family_item_label(data))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, dict(data))
            self._family.addItem(item)
            fit_list_item(self._family, item)
        self._family.blockSignals(False)
        self._refresh_summary()
        self._status.setText(
            "Check related forms; one card is created per type (e.g. nouns, verbs)."
        )

    def _fill_pattern(self, payload: WordPatternPayload) -> None:
        self._pattern_payload = payload
        self._gap.setPlainText(str(payload.get("gap") or ""))
        self._vietnamese.setText(str(payload.get("vietnamese") or ""))
        self._answer.setText(str(payload.get("answer") or ""))
        self._pattern.setText(str(payload.get("pattern") or ""))
        self._explanation.setPlainText(str(payload.get("explanation") or ""))
        self._examples.setPlainText(as_text(payload.get("examples"), multiline=True))
        self._status.setText("Edit the gap card if needed, then create.")

    def _edit_definition(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, dict):
            editor = DefinitionDetailDialog(
                data, str((self._normal_payload or {}).get("word") or ""), self
            )
            if editor.exec():
                data = editor.result_data()
                item.setData(Qt.ItemDataRole.UserRole, data)
                item.setText(item_label(data))
                fit_list_item(self._definitions, item)

    def _edit_family(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, dict):
            editor = FamilyMemberDialog(data, self)
            if editor.exec():
                data = editor.result_data()
                item.setData(Qt.ItemDataRole.UserRole, data)
                item.setText(family_item_label(data))
                fit_list_item(self._family, item)
                self._refresh_summary()

    def _selected_definitions(self) -> list[DefinitionResult]:
        return [
            cast(
                DefinitionResult,
                self._definitions.item(index).data(Qt.ItemDataRole.UserRole),
            )
            for index in range(self._definitions.count())
            if self._definitions.item(index).checkState() == Qt.CheckState.Checked
        ]

    def _form_data(self) -> WordFormPayload:
        others = [
            cast(
                WordFormItem,
                self._family.item(index).data(Qt.ItemDataRole.UserRole),
            )
            for index in range(self._family.count())
            if self._family.item(index).checkState() == Qt.CheckState.Checked
        ]
        return {
            "rootWord": {
                "word": self._root_word.text().strip(),
                "type": self._root_type.text().strip(),
                "ipa": self._root_ipa.text().strip(),
                "definition": self._root_definition.toPlainText().strip(),
                "vietnamese": self._root_vietnamese.text().strip(),
                "popularity": parse_score(self._root_popularity.text()),
                "difficulty": parse_score(self._root_difficulty.text()),
            },
            "other": others,
        }

    def _pattern_data(self) -> WordPatternPayload:
        return {
            "gap": self._gap.toPlainText().strip(),
            "vietnamese": self._vietnamese.text().strip(),
            "answer": self._answer.text().strip(),
            "pattern": self._pattern.text().strip(),
            "explanation": self._explanation.toPlainText().strip(),
            "examples": split_list(self._examples.toPlainText(), multiline=True),
        }

    def _refresh_summary(self) -> None:
        cards = word_form_card_summaries(self._form_data())
        self._summary.setText(
            f"Will create {len(cards)} card(s):\n"
            + "\n".join(f"• {card}" for card in cards)
            if cards
            else "Check at least one related form to create cards."
        )

    def _progress(self, current: int, total: int) -> None:
        self._status.setText(f"Generating pronunciation ({current}/{total})…")
        QApplication.processEvents()

    def _create_cards(self) -> None:
        config = addon_config()
        deck_id = current_deck_id()
        if self._card_type() is CardType.NORMAL:
            selected = self._selected_definitions()
            if not selected:
                showWarning("Select at least one definition.", parent=self)
                return
        elif self._card_type() is CardType.WORD_FORM:
            payload = self._form_data()
            if not payload["rootWord"]["word"] or not payload["other"]:
                showWarning("Root word and one related form are required.", parent=self)
                return
        else:
            payload = self._pattern_data()
            if not payload["gap"] or not payload["answer"]:
                showWarning("Gap and answer are required.", parent=self)
                return
        self._busy(True)
        try:
            if self._card_type() is CardType.NORMAL:
                word = str(
                    (self._normal_payload or {}).get("word")
                    or self._active_input().line.text().strip()
                )
                tags = definition_audio_tags(
                    word, selected, config, mw.col.media.write_data, self._progress
                )
                added = add_definition_notes(
                    mw.col, deck_id, word, "", "", tags, selected
                )
            elif self._card_type() is CardType.WORD_FORM:
                root_audio, form_audio = word_form_audio(
                    payload, config, mw.col.media.write_data, self._progress
                )
                added = add_word_form_notes(
                    mw.col, deck_id, payload, root_audio, form_audio
                )
            else:
                added = add_word_pattern_note(mw.col, deck_id, payload)
        except Exception as exc:
            message = f"Could not create cards: {exc}"
            self._status.setText(message)
            showWarning(message, parent=self)
            self._busy(False)
            return
        mw.reset()
        tooltip(f"Added {added} card(s) to the current deck.", parent=mw)
        self._busy(False)
        self._clear()
        self._active_input().line.clear()
        self._active_input().line.setFocus()
        self._status.setText(f"Created {added} card(s) in the current deck.")


def open_lookup_dialog() -> None:
    if mw.col is None:
        showWarning("Open a profile / collection first.")
        return
    ensure_all_note_types(mw.col)
    LookupDialog(mw).exec()
