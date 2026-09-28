import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  clearToken,
  createWord,
  deleteWord,
  getToken,
  listWords,
  login,
} from "./api";
import { TYPE_LABELS, WORD_TYPES, type Word, type WordType } from "./types";
import "./App.css";

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function App() {
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [password, setPassword] = useState("");
  const [words, setWords] = useState<Word[]>([]);
  const [input, setInput] = useState("");
  const [type, setType] = useState<WordType>("normal");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingList, setLoadingList] = useState(false);

  const refresh = useCallback(async () => {
    setLoadingList(true);
    setError("");
    try {
      setWords(await listWords());
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        clearToken();
        setTokenState(null);
      }
      setError(err instanceof Error ? err.message : "Failed to load words");
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      void refresh();
    }
  }, [token, refresh]);

  async function onLogin(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const next = await login(password);
      setPassword("");
      setTokenState(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  async function onAdd(event: React.FormEvent) {
    event.preventDefault();
    const cleaned = input.trim();
    if (!cleaned) {
      setError("Enter a word or phrase");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await createWord(cleaned, type);
      setInput("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add word");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: string) {
    setBusy(true);
    setError("");
    try {
      await deleteWord(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete");
    } finally {
      setBusy(false);
    }
  }

  function onLogout() {
    clearToken();
    setTokenState(null);
    setWords([]);
    setError("");
  }

  if (!token) {
    return (
      <div className="app">
        <header className="header">
          <h1>Word Inbox</h1>
          <p className="sub">Personal vocabulary capture</p>
        </header>
        <form className="card" onSubmit={onLogin}>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="App password"
              disabled={busy}
            />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button type="submit" disabled={busy || !password}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header row">
        <div>
          <h1>Word Inbox</h1>
          <p className="sub">Capture for later Anki sync</p>
        </div>
        <button type="button" className="ghost" onClick={onLogout}>
          Log out
        </button>
      </header>

      <form className="card add" onSubmit={onAdd}>
        <label className="field">
          <span>Input</span>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Word, phrase, or sentence…"
            autoFocus
            disabled={busy}
          />
        </label>
        <label className="field">
          <span>Type</span>
          <div className="chips">
            {WORD_TYPES.map((value) => (
              <button
                key={value}
                type="button"
                className={type === value ? "chip active" : "chip"}
                onClick={() => setType(value)}
                disabled={busy}
              >
                {TYPE_LABELS[value]}
              </button>
            ))}
          </div>
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={busy || !input.trim()}>
          {busy ? "Saving…" : "Add note"}
        </button>
      </form>

      <section className="card list">
        <div className="row list-head">
          <h2>Inbox</h2>
          <button
            type="button"
            className="ghost"
            onClick={() => void refresh()}
            disabled={loadingList || busy}
          >
            Refresh
          </button>
        </div>
        {loadingList && words.length === 0 ? (
          <p className="muted">Loading…</p>
        ) : null}
        {!loadingList && words.length === 0 ? (
          <p className="muted">No notes yet. Add one above.</p>
        ) : null}
        <ul>
          {words.map((word) => (
            <li key={word.id} className="item">
              <div className="item-main">
                <div className="item-input">{word.input}</div>
                <div className="item-meta">
                  <span className="badge">{TYPE_LABELS[word.type] ?? word.type}</span>
                  <span>{formatTime(word.createdAt)}</span>
                </div>
              </div>
              <button
                type="button"
                className="danger"
                onClick={() => void onDelete(word.id)}
                disabled={busy}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
