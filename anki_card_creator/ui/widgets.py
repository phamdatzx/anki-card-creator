from __future__ import annotations

from collections.abc import Callable

from aqt.qt import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMouseEvent,
    QPushButton,
    QSize,
    Qt,
    QWidget,
)
from aqt.utils import qconnect


class InputPanel(QWidget):
    def __init__(
        self, placeholder: str, on_lookup: Callable[[], None], parent=None
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.line = QLineEdit()
        self.line.setPlaceholderText(placeholder)
        self.button = QPushButton("Look up")
        layout.addWidget(self.line, stretch=1)
        layout.addWidget(self.button)
        qconnect(self.line.returnPressed, on_lookup)
        qconnect(self.button.clicked, on_lookup)


class CheckToggleListWidget(QListWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._press_item: QListWidgetItem | None = None
        self._press_state: Qt.CheckState | None = None

    @staticmethod
    def _event_pos(event: QMouseEvent):
        position = event.position() if hasattr(event, "position") else event.pos()
        return position.toPoint() if hasattr(position, "toPoint") else position

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        item = self.itemAt(self._event_pos(event))
        self._press_item = item
        self._press_state = item.checkState() if item is not None else None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        super().mouseReleaseEvent(event)
        if event.button() != Qt.MouseButton.LeftButton:
            return
        item = self.itemAt(self._event_pos(event))
        if (
            item is None
            or item is not self._press_item
            or self._press_state is None
            or not (item.flags() & Qt.ItemFlag.ItemIsUserCheckable)
        ):
            return
        if item.checkState() == self._press_state:
            item.setCheckState(
                Qt.CheckState.Unchecked
                if self._press_state == Qt.CheckState.Checked
                else Qt.CheckState.Checked
            )


def fit_list_item(list_widget: QListWidget, item: QListWidgetItem) -> None:
    width = max(list_widget.viewport().width() - 28, 80)
    bounds = list_widget.fontMetrics().boundingRect(
        0,
        0,
        width,
        10_000,
        Qt.TextFlag.TextWordWrap | Qt.TextFlag.TextExpandTabs,
        item.text(),
    )
    item.setSizeHint(QSize(width, bounds.height() + 10))


def refit_list(list_widget: QListWidget) -> None:
    for index in range(list_widget.count()):
        item = list_widget.item(index)
        if item is not None:
            fit_list_item(list_widget, item)
