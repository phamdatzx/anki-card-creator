/** Deck manager popup: create, rename, and delete decks. */

import { useState } from "react";
import * as api from "./api";
import { Modal } from "./modal";
import type { Deck, SyncState } from "./types";

const DEFAULT_DECK_ID = 1;

type RowMode = { id: number; kind: "rename"; name: string } | { id: number; kind: "delete" };

export function DeckManager({
  decks,
  onClose,
  onChanged,
}: {
  decks: Deck[];
  onClose: () => void;
  /** Called after every change; `select` is a deck to switch to. */
  onChanged: (sync: SyncState, select?: number) => Promise<void>;
}) {
  const [newName, setNewName] = useState("");
  const [mode, setMode] = useState<RowMode | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  const create = (event: React.FormEvent) => {
    event.preventDefault();
    void run(async () => {
      const { deck, sync } = await api.createDeck(newName);
      setNewName("");
      await onChanged(sync, deck.id);
    });
  };

  const rename = (id: number, name: string) =>
    run(async () => {
      const { sync } = await api.renameDeck(id, name);
      setMode(null);
      await onChanged(sync);
    });

  const remove = (id: number) =>
    run(async () => {
      const { sync } = await api.deleteDeck(id);
      setMode(null);
      await onChanged(sync);
    });

  return (
    <Modal title="Decks" onClose={onClose}>
      <form className="deck-new" onSubmit={create}>
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="New deck (Parent::Child for a subdeck)"
          disabled={busy}
          aria-label="New deck name"
        />
        <button type="submit" className="primary" disabled={busy || !newName.trim()}>
          Create
        </button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      <ul className="deck-list">
        {decks.map((deck) => {
          const depth = deck.name.split("::").length - 1;
          const label = deck.name.split("::").pop();
          const rowMode = mode?.id === deck.id ? mode : null;
          return (
            <li key={deck.id} className="deck-row" style={{ paddingLeft: `${depth * 1.1}rem` }}>
              {rowMode?.kind === "rename" ? (
                <form
                  className="deck-edit"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void rename(deck.id, rowMode.name);
                  }}
                >
                  <input
                    value={rowMode.name}
                    onChange={(e) => setMode({ ...rowMode, name: e.target.value })}
                    disabled={busy}
                    autoFocus
                    aria-label={`New name for ${deck.name}`}
                  />
                  <button type="button" className="ghost small" onClick={() => setMode(null)} disabled={busy}>
                    Cancel
                  </button>
                  <button type="submit" className="primary small" disabled={busy || !rowMode.name.trim()}>
                    Save
                  </button>
                </form>
              ) : rowMode?.kind === "delete" ? (
                <div className="deck-confirm">
                  <p>
                    Delete <strong>{deck.name}</strong>
                    {deck.cards ? (
                      <>
                        {" "}and its <strong>{deck.cards} card(s)</strong>
                      </>
                    ) : null}
                    , including any subdecks? After the next sync this also happens on your other
                    devices.
                  </p>
                  <div className="row end">
                    <button type="button" className="ghost small" onClick={() => setMode(null)} disabled={busy}>
                      Cancel
                    </button>
                    <button type="button" className="danger small" onClick={() => void remove(deck.id)} disabled={busy}>
                      Delete
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="deck-info">
                    <span className="deck-name" title={deck.name}>
                      {label}
                    </span>
                    <span className="muted small-text">{deck.cards} card(s)</span>
                  </div>
                  <div className="deck-actions">
                    <button
                      type="button"
                      className="ghost small"
                      onClick={() => setMode({ id: deck.id, kind: "rename", name: deck.name })}
                      disabled={busy}
                    >
                      Rename
                    </button>
                    <button
                      type="button"
                      className="danger small"
                      onClick={() => setMode({ id: deck.id, kind: "delete" })}
                      disabled={busy || deck.id === DEFAULT_DECK_ID}
                      title={deck.id === DEFAULT_DECK_ID ? "The Default deck can't be deleted" : undefined}
                    >
                      Delete
                    </button>
                  </div>
                </>
              )}
            </li>
          );
        })}
      </ul>
    </Modal>
  );
}
