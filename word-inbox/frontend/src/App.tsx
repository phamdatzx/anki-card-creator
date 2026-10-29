import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "./api";
import { DeckManager } from "./decks";
import { FieldsForm } from "./editors";
import {
  PATTERN_FIELDS,
  SENTENCE_FIELDS,
  picked,
  type Draft,
  type Picked,
} from "./forms";
import {
  CollocationList,
  DefinitionGroupList,
  type DefinitionGroup,
  PhraseList,
  VietnameseList,
} from "./panels";
import { asText, splitList } from "./text";
import {
  CARD_TYPES,
  HINTS,
  PLACEHOLDERS,
  TYPE_LABELS,
  type CardType,
  type CollocationItem,
  type PhraseSense,
  type Deck,
  type LookupResponse,
  type ModelState,
  type SyncState,
  type VietnameseResult,
} from "./types";
import "./App.css";

type Result =
  | {
      type: "normal";
      input: string;
      inputNote: string;
      word: string;
      groups: DefinitionGroup[];
      family: Picked<VietnameseResult>[];
    }
  | { type: "vietnamese"; query: string; items: Picked<VietnameseResult>[] }
  | { type: "word_pattern"; draft: Draft }
  | { type: "sentence"; draft: Draft }
  | { type: "collocation"; keyword: string; items: Picked<CollocationItem>[] }
  | { type: "phrase"; phrase: string; items: Picked<PhraseSense>[] };

type Status = { text: string; tone: "info" | "error" | "success" };

const DECK_KEY = "word-inbox-deck";

function savedDeckId(): number | null {
  try {
    const value = Number(localStorage.getItem(DECK_KEY));
    return Number.isInteger(value) && value > 0 ? value : null;
  } catch {
    return null;
  }
}

/** Keep each pattern's collocations together, patterns in first-seen order. */
function byPattern(items: CollocationItem[]): CollocationItem[] {
  const order = [...new Set(items.map((item) => item.pattern.trim().toLowerCase()))];
  return [...items].sort(
    (a, b) =>
      order.indexOf(a.pattern.trim().toLowerCase()) - order.indexOf(b.pattern.trim().toLowerCase()),
  );
}

function toResult(response: LookupResponse): { result: Result | null; message: string } {
  switch (response.type) {
    case "normal": {
      const { input, inputNote, word, groups, family } = response.payload;
      return groups.length || family.length
        ? {
            // Cards start unticked as before; the parts inside a card start ticked.
            result: {
              type: "normal",
              input,
              inputNote,
              word,
              groups: picked(
                groups.map((parts) => picked(parts, true)),
                false,
              ),
              family: picked(family, false),
            },
            message:
              "Each box is one card; related parts of speech share one. Tick the root's cards and any family words to learn.",
          }
        : { result: null, message: `No definitions for "${word}".` };
    }
    case "vietnamese": {
      const { query, results } = response.payload;
      return results.length
        ? { result: { type: "vietnamese", query, items: picked(results, false) }, message: "Select matching words; click Edit to change one." }
        : { result: null, message: `No matching English words for "${query}".` };
    }
    case "word_pattern": {
      const payload = response.payload;
      return {
        result: { type: "word_pattern", draft: { ...payload, examples: asText(payload.examples, true) } },
        message: "Edit the gap card if needed, then create.",
      };
    }
    case "sentence":
      return {
        result: { type: "sentence", draft: { ...response.payload } },
        message: "Edit the translation if needed, then create.",
      };
    case "collocation": {
      const { keyword, items } = response.payload;
      return items.length
        ? {
            result: { type: "collocation", keyword, items: picked(byPattern(items), false) },
            message: "Tick the collocations to learn; each becomes one gap card.",
          }
        : { result: null, message: `No collocations found for "${keyword}".` };
    }
    case "phrase": {
      const { phrase, results } = response.payload;
      return results.length
        ? {
            // A single meaning is almost always wanted; preselect it.
            result: { type: "phrase", phrase, items: picked(results, results.length === 1) },
            message: "Tick the meanings to learn; each becomes one recall card.",
          }
        : { result: null, message: `No meanings found for "${phrase}".` };
    }
  }
}

/** Ticked cards, each with only its ticked parts; empty cards are dropped. */
function normalGroups(groups: DefinitionGroup[]) {
  return groups
    .filter((group) => group.checked)
    .map((group) => group.data.filter((part) => part.checked).map((part) => part.data))
    .filter((parts) => parts.length > 0);
}

function toPayload(result: Result): unknown {
  const checked = <T,>(items: Picked<T>[]) =>
    items.filter((item) => item.checked).map((item) => item.data);
  switch (result.type) {
    case "normal":
      return {
        word: result.word,
        groups: normalGroups(result.groups),
        family: checked(result.family),
      };
    case "vietnamese":
      return { query: result.query, results: checked(result.items) };
    case "word_pattern": {
      const draft = result.draft;
      return {
        gap: draft.gap.trim(),
        vietnamese: draft.vietnamese.trim(),
        answer: draft.answer.trim(),
        pattern: draft.pattern.trim(),
        explanation: draft.explanation.trim(),
        examples: splitList(draft.examples, true),
      };
    }
    case "sentence":
      return { vietnamese: result.draft.vietnamese, sentence: result.draft.sentence };
    case "collocation":
      return { keyword: result.keyword, items: checked(result.items) };
    case "phrase":
      return { phrase: result.phrase, results: checked(result.items) };
  }
}

function syncLabel(state: SyncState | null): string {
  if (!state || !state.enabled) {
    return "AnkiWeb sync off";
  }
  if (state.at === null) {
    return "Not synced yet";
  }
  const time = new Date(state.at * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return state.ok ? `Synced ${time}` : `Sync failed ${time}`;
}

function Login({ onDone }: { onDone: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.login(password);
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="app">
      <header className="header">
        <h1>Word Inbox</h1>
        <p className="sub">Anki cards from anywhere</p>
      </header>
      <form className="card" onSubmit={submit}>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={busy}
            autoFocus
          />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" className="primary wide" disabled={busy || !password}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}

export default function App() {
  const [signedIn, setSignedIn] = useState(() => api.getToken() !== null);
  const [cardType, setCardType] = useState<CardType>("normal");
  const [input, setInput] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [status, setStatus] = useState<Status>({ text: HINTS.normal, tone: "info" });
  const [busy, setBusy] = useState<"" | "lookup" | "create" | "sync" | "model">("");
  const [decks, setDecks] = useState<Deck[]>([]);
  const [deckId, setDeckId] = useState<number | null>(savedDeckId);
  const [sync, setSync] = useState<SyncState | null>(null);
  const [managingDecks, setManagingDecks] = useState(false);
  const [models, setModels] = useState<ModelState | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  // undefined until the first status arrives, so decks load even without sync.
  const lastSyncAt = useRef<number | null | undefined>(undefined);

  const fail = useCallback((err: unknown, fallback: string) => {
    if (err instanceof api.ApiError && err.status === 401) {
      api.clearToken();
      setSignedIn(false);
    }
    setStatus({ text: err instanceof Error ? err.message : fallback, tone: "error" });
  }, []);

  const loadDecks = useCallback(async () => {
    try {
      const data = await api.decks();
      setDecks(data.decks);
      setDeckId((current) =>
        current !== null && data.decks.some((deck) => deck.id === current)
          ? current
          : (data.defaultDeckId ?? data.decks[0]?.id ?? null),
      );
    } catch (err) {
      fail(err, "Could not load decks");
    }
  }, [fail]);

  const applySync = useCallback(
    (state: SyncState) => {
      setSync(state);
      // A sync (especially the first download) can change the deck list.
      if (state.at !== lastSyncAt.current) {
        lastSyncAt.current = state.at;
        void loadDecks();
      }
    },
    [loadDecks],
  );

  useEffect(() => {
    if (!signedIn) {
      return;
    }
    const refresh = () =>
      Promise.all([
        api.status().then(
          (data) => applySync(data.sync),
          (err: unknown) => fail(err, "Could not load status"),
        ),
        // Polled too, so a server restart (back to the default) shows up here.
        api.getModel().then(setModels, (err: unknown) => fail(err, "Could not load models")),
      ]);
    void refresh();
    const timer = window.setInterval(refresh, 30_000);
    return () => window.clearInterval(timer);
  }, [signedIn, applySync, fail]);

  useEffect(() => {
    try {
      if (deckId !== null) {
        localStorage.setItem(DECK_KEY, String(deckId));
      }
    } catch {
      // Remembering the deck is a convenience only.
    }
  }, [deckId]);

  async function chooseModel(next: string) {
    if (!models || next === models.model) {
      return;
    }
    const previous = models;
    setModels({ ...models, model: next });
    setBusy("model");
    try {
      setModels(await api.setModel(next));
      setStatus({ text: `Lookups now use ${next}.`, tone: "success" });
    } catch (err) {
      setModels(previous);
      fail(err, "Could not change the model");
    } finally {
      setBusy("");
    }
  }

  function chooseType(next: CardType) {
    setCardType(next);
    setResult(null);
    setStatus({ text: HINTS[next], tone: "info" });
  }

  async function onLookup(event: React.FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) {
      return;
    }
    setResult(null);
    setBusy("lookup");
    setStatus({ text: "Looking up…", tone: "info" });
    try {
      const { result: next, message } = toResult(await api.lookup(cardType, text));
      setResult(next);
      setStatus({ text: message, tone: "info" });
    } catch (err) {
      fail(err, "Lookup failed");
    } finally {
      setBusy("");
    }
  }

  async function onCreate() {
    if (!result || busy) {
      return;
    }
    if (deckId === null) {
      setStatus({ text: "Choose a deck first.", tone: "error" });
      return;
    }
    setBusy("create");
    setStatus({ text: "Generating pronunciation and creating cards…", tone: "info" });
    try {
      const created = await api.createCards(result.type, deckId, toPayload(result));
      applySync(created.sync);
      const syncNote = !created.sync.enabled
        ? ""
        : created.sync.ok
          ? " · synced to AnkiWeb"
          : ` · ${created.sync.message}`;
      setStatus({
        text: `Created ${created.added} card(s) in ${created.deck}${syncNote}`,
        tone: created.sync.enabled && !created.sync.ok ? "error" : "success",
      });
      setResult(null);
      setInput("");
      inputRef.current?.focus();
    } catch (err) {
      fail(err, "Could not create cards");
    } finally {
      setBusy("");
    }
  }

  async function onSync(forceDownload = false) {
    if (
      forceDownload &&
      !window.confirm(
        "Replace the server's collection with the one on AnkiWeb? Cards the server never uploaded will be lost.",
      )
    ) {
      return;
    }
    setBusy("sync");
    try {
      applySync((await api.sync(forceDownload)).sync);
    } catch (err) {
      fail(err, "Sync failed");
    } finally {
      setBusy("");
    }
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      void onCreate();
    }
  }

  function logout() {
    api.clearToken();
    setSignedIn(false);
    setResult(null);
  }

  if (!signedIn) {
    return <Login onDone={() => setSignedIn(true)} />;
  }

  const canCreate =
    result !== null &&
    (result.type === "normal"
      ? normalGroups(result.groups).length > 0 || result.family.some((item) => item.checked)
      : !("items" in result && result.items.every((item) => !item.checked)));

  return (
    <div className="app" onKeyDown={onKeyDown}>
      <header className="header row">
        <div>
          <h1>Word Inbox</h1>
          <p className="sub">Anki cards from anywhere</p>
        </div>
        <button type="button" className="ghost small" onClick={logout}>
          Log out
        </button>
      </header>

      <section className="card toolbar">
        <div className="field inline">
          <label htmlFor="deck">Deck</label>
          <div className="deck-picker">
            <select
              id="deck"
              value={deckId ?? ""}
              onChange={(e) => setDeckId(Number(e.target.value))}
              disabled={busy !== "" || decks.length === 0}
            >
              {decks.length === 0 ? <option value="">Loading…</option> : null}
              {decks.map((deck) => (
                <option key={deck.id} value={deck.id}>
                  {deck.name}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="ghost small"
              onClick={() => setManagingDecks(true)}
              disabled={busy !== "" || decks.length === 0}
            >
              Manage
            </button>
          </div>
        </div>
        <div className="field inline">
          <label htmlFor="model">Model</label>
          <select
            id="model"
            value={models?.model ?? ""}
            onChange={(e) => void chooseModel(e.target.value)}
            disabled={busy !== "" || !models || models.choices.length < 2}
            title={
              models && models.choices.length < 2
                ? "Add more models to OPENAI_MODELS on the server to switch"
                : "Used for lookups until the server restarts"
            }
          >
            {!models ? <option value="">Loading…</option> : null}
            {models?.choices.map((name) => (
              <option key={name} value={name}>
                {name === models.default ? `${name} (default)` : name}
              </option>
            ))}
          </select>
        </div>
        <div className="sync">
          <span className={sync?.ok === false ? "sync-label bad" : "sync-label"} title={sync?.message}>
            {busy === "sync" ? "Syncing…" : syncLabel(sync)}
          </span>
          {sync?.enabled ? (
            <button type="button" className="ghost small" onClick={() => void onSync()} disabled={busy !== ""}>
              Sync now
            </button>
          ) : null}
        </div>
        {sync?.ok === false ? <p className="error full">{sync.message}</p> : null}
        {sync?.needs_forced_download ? (
          <button type="button" className="danger small full" onClick={() => void onSync(true)} disabled={busy !== ""}>
            Download from AnkiWeb (discard unsynced server cards)
          </button>
        ) : null}
      </section>

      <form className="card" onSubmit={onLookup}>
        <div className="chips" role="radiogroup" aria-label="Card type">
          {CARD_TYPES.map((value) => (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={cardType === value}
              className={cardType === value ? "chip active" : "chip"}
              onClick={() => chooseType(value)}
              disabled={busy !== ""}
            >
              {TYPE_LABELS[value]}
            </button>
          ))}
        </div>
        <div className="lookup">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={PLACEHOLDERS[cardType]}
            disabled={busy !== ""}
            autoFocus
            enterKeyHint="search"
          />
          <button type="submit" className="primary" disabled={busy !== "" || !input.trim()}>
            {busy === "lookup" ? "Looking up…" : "Look up"}
          </button>
        </div>
        <p className={`status ${status.tone}`}>{status.text}</p>
      </form>

      {result ? (
        <section className="card results">
          {result.type === "normal" ? (
            <>
              <h2>{result.word}</h2>
              {result.inputNote ? (
                <p className="muted input-note">
                  You entered: <strong>{result.input}</strong> ({result.inputNote})
                </p>
              ) : null}
              <DefinitionGroupList
                groups={result.groups}
                onChange={(groups) => setResult({ ...result, groups })}
              />
              {result.family.length ? (
                <>
                  <h3 className="family-title">Word family</h3>
                  <p className="muted small-text">Each word you tick becomes its own card.</p>
                  <VietnameseList
                    items={result.family}
                    onChange={(family) => setResult({ ...result, family })}
                  />
                </>
              ) : null}
            </>
          ) : null}
          {result.type === "vietnamese" ? (
            <VietnameseList items={result.items} onChange={(items) => setResult({ ...result, items })} />
          ) : null}
          {result.type === "word_pattern" ? (
            <FieldsForm fields={PATTERN_FIELDS} draft={result.draft} onChange={(draft) => setResult({ ...result, draft })} />
          ) : null}
          {result.type === "collocation" ? (
            <>
              <h2>{result.keyword}</h2>
              <CollocationList items={result.items} onChange={(items) => setResult({ ...result, items })} />
            </>
          ) : null}
          {result.type === "phrase" ? (
            <>
              <h2>{result.phrase}</h2>
              <PhraseList
                phrase={result.phrase}
                items={result.items}
                onChange={(items) => setResult({ ...result, items })}
              />
            </>
          ) : null}
          {result.type === "sentence" ? (
            <FieldsForm fields={SENTENCE_FIELDS} draft={result.draft} onChange={(draft) => setResult({ ...result, draft })} />
          ) : null}
          <button
            type="button"
            className="primary wide create"
            onClick={() => void onCreate()}
            disabled={busy !== "" || !canCreate}
          >
            {busy === "create" ? "Creating cards…" : "Create cards (Ctrl+Enter)"}
          </button>
        </section>
      ) : null}

      {managingDecks ? (
        <DeckManager
          decks={decks}
          onClose={() => setManagingDecks(false)}
          onChanged={async (state, select) => {
            applySync(state);
            await loadDecks();
            if (select !== undefined) {
              setDeckId(select);
            }
          }}
        />
      ) : null}
    </div>
  );
}
