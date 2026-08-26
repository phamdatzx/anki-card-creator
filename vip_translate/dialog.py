from __future__ import annotations

from typing import Any

from aqt import mw
from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    Qt,
    QTextEdit,
    QVBoxLayout,
)
from aqt.utils import qconnect, showInfo, showWarning, tooltip

from .api import WordsApiError, fetch_word
from .cards import add_definition_notes, ensure_note_type


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


def _item_label(result: dict[str, Any]) -> str:
    pos = result.get("partOfSpeech") or "?"
    definition = result.get("definition") or ""
    return f"[{pos}] {definition}"


class DefinitionDetailDialog(QDialog):
    def __init__(self, result: dict[str, Any], word: str = "", parent=None) -> None:
        super().__init__(parent or mw)
        title = f"Edit definition — {word}" if word else "Edit definition"
        self.setWindowTitle(title)
        self.resize(480, 360)
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

        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.addRow("Definition:", self._definition)
        form.addRow("Part of speech:", self._pos)
        form.addRow("Synonyms:", self._synonyms)
        form.addRow("Examples:", self._examples)

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
        self.setWindowTitle("VIP Translate")
        self.resize(560, 480)
        self._payload: dict[str, Any] | None = None

        self._word_input = QLineEdit()
        self._word_input.setPlaceholderText("Enter a word…")
        self._lookup_btn = QPushButton("Look up")
        self._status = QLabel("Enter a word, then look it up.")
        self._status.setWordWrap(True)

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        self._create_btn = QPushButton("Create cards")
        self._create_btn.setEnabled(False)
        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)

        word_row = QHBoxLayout()
        word_row.addWidget(self._word_input, stretch=1)
        word_row.addWidget(self._lookup_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(word_row)
        layout.addWidget(self._status)
        layout.addWidget(self._list, stretch=1)
        layout.addWidget(self._create_btn)
        layout.addWidget(close_box)

        qconnect(self._lookup_btn.clicked, self._on_lookup)
        qconnect(self._word_input.returnPressed, self._on_lookup)
        qconnect(self._list.itemDoubleClicked, self._on_item_double_clicked)
        qconnect(self._create_btn.clicked, self._on_create)
        qconnect(close_box.rejected, self.reject)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
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

    def _on_lookup(self) -> None:
        word = self._word_input.text().strip()
        config = _addon_config()
        self._list.clear()
        self._payload = None
        self._create_btn.setEnabled(False)
        self._status.setText("Looking up…")
        self._lookup_btn.setEnabled(False)

        try:
            payload = fetch_word(
                word,
                api_key=str(config.get("rapidapi_key") or ""),
                host=str(config.get("rapidapi_host") or "wordsapiv1.p.rapidapi.com"),
                verify_ssl=bool(config.get("verify_ssl", False)),
            )
        except WordsApiError as exc:
            self._status.setText(str(exc))
            showWarning(str(exc), parent=self)
            return
        finally:
            self._lookup_btn.setEnabled(True)

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
            self._list.addItem(item)

        pronunciation = _pronunciation_text(payload)
        syllable_count = _syllable_count_text(payload)
        suffix_parts = []
        if pronunciation:
            suffix_parts.append(pronunciation)
        if syllable_count:
            suffix_parts.append(f"{syllable_count} syllables")
        suffix = f" · {' · '.join(suffix_parts)}" if suffix_parts else ""
        self._status.setText(
            f'{payload.get("word", word)}{suffix} — double-click to edit; '
            "check definitions, then create cards."
        )
        self._create_btn.setEnabled(True)

    def _selected_results(self) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, dict):
                    selected.append(data)
        return selected

    def _on_create(self) -> None:
        if not self._payload:
            showWarning("Look up a word first.", parent=self)
            return

        selected = self._selected_results()
        if not selected:
            showWarning("Select at least one definition.", parent=self)
            return

        word = str(self._payload.get("word") or self._word_input.text().strip())
        pronunciation = _pronunciation_text(self._payload)
        syllable_count = _syllable_count_text(self._payload)

        try:
            deck_id = int(mw.col.decks.get_current_id())
        except AttributeError:
            deck_id = int(mw.col.decks.current()["id"])

        try:
            added = add_definition_notes(
                mw.col,
                deck_id,
                word,
                pronunciation,
                syllable_count,
                selected,
            )
        except Exception as exc:  # noqa: BLE001 - show to user
            showWarning(f"Could not create cards: {exc}", parent=self)
            return

        mw.reset()
        tooltip(f"Added {added} card(s) to the current deck.", parent=mw)
        showInfo(f"Created {added} card(s) in the current deck.", parent=self)
        self.accept()


def open_lookup_dialog() -> None:
    if mw.col is None:
        showWarning("Open a profile / collection first.")
        return
    ensure_note_type(mw.col)
    dialog = LookupDialog(mw)
    dialog.exec()
