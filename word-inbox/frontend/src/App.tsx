import { useEffect, useState } from "react";
import { ApiError, clearToken, getToken, login, sendBatch } from "./api";
import {
  MAX_BATCH_SIZE,
  TYPE_LABELS,
  WORD_TYPES,
  type PendingWord,
  type WordType,
} from "./types";
import "./App.css";

const QUEUE_KEY = "word-inbox-queue";

function loadQueue(): PendingWord[] {
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? (parsed as PendingWord[]) : [];
  } catch {
    return [];
  }
}

export default function App() {
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [password, setPassword] = useState("");
  const [queue, setQueue] = useState<PendingWord[]>(loadQueue);
  const [input, setInput] = useState("");
  const [type, setType] = useState<WordType>("normal");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
    } catch {
      // Storage unavailable; the queue still works for this session.
    }
  }, [queue]);

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

  function onAdd(event: React.FormEvent) {
    event.preventDefault();
    const cleaned = input.trim();
    if (!cleaned) {
      return;
    }
    if (queue.length >= MAX_BATCH_SIZE) {
      setError(`At most ${MAX_BATCH_SIZE} words per batch — send first.`);
      return;
    }
    setQueue((prev) => [
      ...prev,
      { key: crypto.randomUUID(), input: cleaned, type },
    ]);
    setInput("");
    setError("");
    setNotice("");
  }

  function onRemove(key: string) {
    setQueue((prev) => prev.filter((item) => item.key !== key));
  }

  function onChangeType(key: string, next: WordType) {
    setQueue((prev) =>
      prev.map((item) => (item.key === key ? { ...item, type: next } : item)),
    );
  }

  async function onSend() {
    if (queue.length === 0) {
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await sendBatch(
        queue.map(({ input, type }) => ({ input, type })),
      );
      setQueue([]);
      setNotice(`Sent ${result.count} word${result.count === 1 ? "" : "s"}.`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        clearToken();
        setTokenState(null);
      }
      setError(err instanceof Error ? err.message : "Could not send batch");
    } finally {
      setBusy(false);
    }
  }

  function onLogout() {
    clearToken();
    setTokenState(null);
    setError("");
    setNotice("");
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
            placeholder="Word, phrase, or sentence… (Enter to add)"
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
        <button type="submit" disabled={busy || !input.trim()}>
          Add to batch
        </button>
      </form>

      <section className="card list">
        <div className="row list-head">
          <h2>
            Batch <span className="muted">({queue.length})</span>
          </h2>
          <button
            type="button"
            className="ghost"
            onClick={() => setQueue([])}
            disabled={busy || queue.length === 0}
          >
            Clear
          </button>
        </div>
        {queue.length === 0 ? (
          <p className="muted">Nothing queued. Add words above, then send.</p>
        ) : null}
        <ul>
          {queue.map((item) => (
            <li key={item.key} className="item">
              <div className="item-main">
                <div className="item-input">{item.input}</div>
                <div className="item-meta">
                  <select
                    className="badge"
                    value={item.type}
                    onChange={(e) =>
                      onChangeType(item.key, e.target.value as WordType)
                    }
                    disabled={busy}
                    aria-label={`Type for ${item.input}`}
                  >
                    {WORD_TYPES.map((value) => (
                      <option key={value} value={value}>
                        {TYPE_LABELS[value]}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <button
                type="button"
                className="danger"
                onClick={() => onRemove(item.key)}
                disabled={busy}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
        {error ? <p className="error">{error}</p> : null}
        {notice ? <p className="notice">{notice}</p> : null}
        <button
          type="button"
          className="send"
          onClick={() => void onSend()}
          disabled={busy || queue.length === 0}
        >
          {busy
            ? "Sending…"
            : `Send ${queue.length || ""} word${queue.length === 1 ? "" : "s"}`}
        </button>
      </section>
    </div>
  );
}
