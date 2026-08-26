from __future__ import annotations

from collections.abc import Callable

from aqt import gui_hooks, mw
from aqt.qt import QAction
from aqt.utils import qconnect

from .dialog import open_lookup_dialog

LINK_CMD = "vip_translate"


def _on_overview_bottom(
    link_handler: Callable[[str], bool], links: list[list[str]]
) -> Callable[[str], bool]:
    links.append(["V", LINK_CMD, "VIP Translate"])

    def custom_link_handler(url: str) -> bool:
        if url == LINK_CMD:
            open_lookup_dialog()
            return True
        return link_handler(url)

    return custom_link_handler


gui_hooks.overview_will_render_bottom.append(_on_overview_bottom)

action = QAction("VIP Translate…", mw)
qconnect(action.triggered, open_lookup_dialog)
mw.form.menuTools.addAction(action)
