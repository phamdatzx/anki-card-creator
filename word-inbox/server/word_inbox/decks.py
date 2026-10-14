"""Deck create/rename/delete with the checks Anki itself skips.

Anki silently turns a duplicate rename into "Name+", a blank name into
"blank", and ignores deleting the Default deck, so validate first.
"""

from __future__ import annotations

from typing import Any

DEFAULT_DECK_ID = 1
SEPARATOR = "::"


class DeckError(ValueError):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def clean_name(name: str) -> str:
    """Trim each ``Parent::Child`` part; reject empty parts."""
    parts = [part.strip() for part in name.split(SEPARATOR)]
    if not all(parts):
        raise DeckError("Enter a deck name (use Parent::Child for subdecks).")
    return SEPARATOR.join(parts)


def _deck(col: Any, deck_id: int) -> dict[str, Any]:
    deck = col.decks.get(deck_id, default=False)
    if not deck:
        raise DeckError("That deck no longer exists.", 404)
    if deck.get("dyn"):
        raise DeckError("Filtered decks can't be changed here.")
    return deck


def _taken(col: Any, name: str, except_id: int | None = None) -> bool:
    found = col.decks.id_for_name(name)  # case-insensitive, like Anki's names
    return bool(found) and int(found) != except_id


def list_decks(col: Any) -> list[dict[str, Any]]:
    return [
        {
            "id": int(deck.id),
            "name": deck.name,
            "cards": int(col.decks.card_count(deck.id, include_subdecks=True)),
        }
        for deck in col.decks.all_names_and_ids(include_filtered=False)
    ]


def create_deck(col: Any, name: str) -> dict[str, Any]:
    name = clean_name(name)
    if _taken(col, name):
        raise DeckError(f'A deck named "{name}" already exists.', 409)
    deck_id = int(col.decks.id(name, create=True))
    return {"id": deck_id, "name": col.decks.name(deck_id), "cards": 0}


def rename_deck(col: Any, deck_id: int, name: str) -> dict[str, Any]:
    _deck(col, deck_id)
    name = clean_name(name)
    if _taken(col, name, except_id=deck_id):
        raise DeckError(f'A deck named "{name}" already exists.', 409)
    col.decks.rename(deck_id, name)
    return {
        "id": deck_id,
        "name": col.decks.name(deck_id),
        "cards": int(col.decks.card_count(deck_id, include_subdecks=True)),
    }


def delete_deck(col: Any, deck_id: int) -> dict[str, Any]:
    """Delete a deck, its subdecks, and all their cards."""
    if deck_id == DEFAULT_DECK_ID:
        raise DeckError("The Default deck can't be deleted.")
    deck = _deck(col, deck_id)
    removed = col.decks.remove([deck_id])
    return {"name": str(deck["name"]), "cards": int(removed.count)}
