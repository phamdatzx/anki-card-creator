from __future__ import annotations

from typing import Any

from aqt import mw
from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)
from aqt.utils import qconnect

from ..text import as_text, parse_score, score_field_text, split_list


class DefinitionDetailDialog(QDialog):
    def __init__(
        self,
        result: dict[str, Any],
        word: str = "",
        parent=None,
        *,
        editable_word: bool = False,
    ) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle(f"Edit definition — {word}" if word else "Edit definition")
        self.resize(480, 400)
        self._original = dict(result)
        self._editable_word = editable_word
        if editable_word:
            self._word = QLineEdit(str(result.get("word") or word or ""))
            self._word.setPlaceholderText("Required")
        self._definition = QTextEdit(str(result.get("definition") or ""))
        self._definition.setMinimumHeight(80)
        self._vietnamese = QLineEdit(str(result.get("vietnamese") or ""))
        self._pos = QLineEdit(str(result.get("partOfSpeech") or ""))
        self._ipa = QLineEdit(str(result.get("ipa") or ""))
        self._ipa.setPlaceholderText("/ˈwɜrd/")
        self._synonyms = QLineEdit(as_text(result.get("synonyms")))
        self._synonyms.setPlaceholderText("comma-separated")
        self._examples = QTextEdit(as_text(result.get("examples"), multiline=True))
        self._examples.setPlaceholderText("one example per line, or comma-separated")
        self._examples.setMinimumHeight(80)
        self._popularity = QLineEdit(score_field_text(result.get("popularity")))
        self._popularity.setPlaceholderText("1–5")
        self._difficulty = QLineEdit(score_field_text(result.get("difficulty")))
        self._difficulty.setPlaceholderText("1–5")
        form = QFormLayout()
        rows: list[tuple[str, Any]] = []
        if editable_word:
            rows.append(("Word:", self._word))
        rows.extend(
            (
                ("Definition:", self._definition),
                ("Vietnamese:", self._vietnamese),
                ("Part of speech:", self._pos),
                ("IPA:", self._ipa),
                ("Synonyms:", self._synonyms),
                ("Examples:", self._examples),
                ("Popularity (1–5):", self._popularity),
                ("Difficulty (1–5):", self._difficulty),
            )
        )
        for label, widget in rows:
            form.addRow(label, widget)
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
        if self._editable_word:
            data["word"] = self._word.text().strip()
        data.update(
            definition=self._definition.toPlainText().strip(),
            vietnamese=self._vietnamese.text().strip(),
            partOfSpeech=self._pos.text().strip(),
            ipa=self._ipa.text().strip(),
            synonyms=split_list(self._synonyms.text()),
            examples=split_list(self._examples.toPlainText(), multiline=True),
            popularity=parse_score(self._popularity.text().strip()),
            difficulty=parse_score(self._difficulty.text().strip()),
        )
        return data


class FamilyMemberDialog(QDialog):
    def __init__(self, item: dict[str, Any], parent=None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("Edit word form")
        self.resize(480, 400)
        self._original = dict(item)
        self._word = QLineEdit(str(item.get("word") or ""))
        self._type = QLineEdit(str(item.get("type") or ""))
        self._ipa = QLineEdit(str(item.get("ipa") or ""))
        self._ipa.setPlaceholderText("/ˈwɜrd/")
        self._vietnamese = QLineEdit(str(item.get("vietnamese") or ""))
        self._vietnamese.setPlaceholderText("Required")
        self._definition = QTextEdit(str(item.get("definition") or ""))
        self._definition.setPlaceholderText("Required")
        self._definition.setMinimumHeight(80)
        self._examples = QTextEdit(as_text(item.get("examples"), multiline=True))
        self._examples.setPlaceholderText("Required; one example per line")
        self._examples.setMinimumHeight(80)
        self._popularity = QLineEdit(score_field_text(item.get("popularity")))
        self._popularity.setPlaceholderText("1–5")
        self._difficulty = QLineEdit(score_field_text(item.get("difficulty")))
        self._difficulty.setPlaceholderText("1–5")
        form = QFormLayout()
        for label, widget in (
            ("Word:", self._word),
            ("Type:", self._type),
            ("IPA:", self._ipa),
            ("Vietnamese:", self._vietnamese),
            ("Definition:", self._definition),
            ("Examples:", self._examples),
            ("Popularity (1–5):", self._popularity),
            ("Difficulty (1–5):", self._difficulty),
        ):
            form.addRow(label, widget)
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
        data.update(
            word=self._word.text().strip(),
            type=self._type.text().strip(),
            ipa=self._ipa.text().strip(),
            vietnamese=self._vietnamese.text().strip(),
            definition=self._definition.toPlainText().strip(),
            examples=split_list(self._examples.toPlainText(), multiline=True),
            popularity=parse_score(self._popularity.text().strip()),
            difficulty=parse_score(self._difficulty.text().strip()),
        )
        return data
