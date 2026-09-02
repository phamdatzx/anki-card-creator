from __future__ import annotations

from collections.abc import Callable

from aqt import gui_hooks, mw
from aqt.qt import QAction
from aqt.utils import qconnect

from .ui.dialog import open_lookup_dialog

LINK_CMD = "anki_card_creator"
_registered = False


def _on_overview_bottom(
    link_handler: Callable[[str], bool], links: list[list[str]]
) -> Callable[[str], bool]:
    links.append(["C", LINK_CMD, "Anki Card Creator"])

    def custom_link_handler(url: str) -> bool:
        if url == LINK_CMD:
            open_lookup_dialog()
            return True
        return link_handler(url)

    return custom_link_handler


def register() -> None:
    global _registered
    if _registered:
        return
    gui_hooks.overview_will_render_bottom.append(_on_overview_bottom)
    action = QAction("Anki Card Creator…", mw)
    qconnect(action.triggered, open_lookup_dialog)
    mw.form.menuTools.addAction(action)
    _registered = True
