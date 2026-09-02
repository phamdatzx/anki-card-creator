"""Anki Card Creator add-on entry point."""

from __future__ import annotations

try:
    from aqt import mw as _mw
except ImportError:
    _mw = None

if _mw is not None:
    from .bootstrap import register

    register()
