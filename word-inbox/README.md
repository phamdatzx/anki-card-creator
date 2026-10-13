# Word Inbox

A single-user web app that does what the Anki Card Creator add-on dialog does,
without desktop Anki:

1. Pick a card type (Normal, Word form, Word pattern, Sentence,
   Vietnamese → English), type a word or sentence, and click **Look up**.
2. Review the results like in the add-on: tick definitions or related forms,
   click **Edit** to change any field, then **Create cards** (Ctrl+Enter).
3. The server generates the pronunciation audio, adds the notes to the deck
   you chose, and syncs with **AnkiWeb**. Your phone and desktop get the cards
   on their next sync.

The server keeps its own Anki collection, opened with the `anki` pip package.
It imports the add-on's pure modules (`anki_card_creator/lookups`, `audio.py`,
`notes/`), so prompts, schemas, and note types (`VIP Translate`,
`VIP Word Form`, …) are identical to the add-on's.

```
word-inbox/
  server/      FastAPI app (word_inbox/) and its tests
  frontend/    Vite + React + TypeScript page
  Dockerfile   one image: built page + API
  docker-compose.yml
  .env.example every setting
```

## Run it on a server

```bash
cd word-inbox
cp .env.example .env      # set APP_PASSWORD, OPENAI_API_KEY, ANKIWEB_*
docker compose up -d --build
```

The app listens on `127.0.0.1:8088`. Put it behind a TLS reverse proxy before
opening it to the internet, for example with Caddy:

```
inbox.example.com {
  reverse_proxy 127.0.0.1:8088
}
```

Everything the server keeps lives in `word-inbox/data/`: `collection.anki2`
and its media, `sync_auth.json` (the AnkiWeb sync key), and `app_secret`.
Back that folder up.

## AnkiWeb sync: first run and safety

- **Sync desktop Anki first.** On its first sync, the server downloads your
  whole collection from AnkiWeb. Large collections take a while, and the page
  shows "Not synced yet" until it finishes.
- After the first login the server stores a sync key, and you can remove
  `ANKIWEB_PASSWORD` from `.env`. The password is used again only if AnkiWeb
  revokes the key.
- Each **Create cards** runs: sync → add cards → sync. If the last sync fails,
  the cards stay on the server and go up with the next sync. Use **Sync now**
  to retry.
- **The server never uploads a whole collection.** When AnkiWeb asks for a
  one-way sync (for example after you change a note type's fields on desktop):
  - The server downloads AnkiWeb's copy if it has no cards of its own waiting
    to sync.
  - If it does have unsynced cards, it stops and shows **Download from AnkiWeb
    (discard unsynced server cards)**. Pick that only if you're fine losing
    those cards. Otherwise look at them first, for example by copying
    `data/collection.anki2` and opening it in Anki.
  - If AnkiWeb asks the server to *upload*, the sync fails. That usually means
    the AnkiWeb account is empty, so sync from desktop Anki first.
- Avoid adding the same word from desktop and from Word Inbox in the same
  sync window. Both copies would sync as separate notes.

Without `ANKIWEB_USERNAME`, sync is off and cards only go into
`data/collection.anki2`.

## Settings

All settings are environment variables; see [`.env.example`](.env.example).

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_PASSWORD` | — (required) | Web login password |
| `APP_SECRET` | random, kept in `data/app_secret` | Signs 30-day login tokens |
| `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`, `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE` | same defaults as the add-on | Lookups and pronunciation audio |
| `VERIFY_SSL` | `true` | TLS certificate checks for the API |
| `ANKIWEB_USERNAME`, `ANKIWEB_PASSWORD` | empty (sync off) | AnkiWeb account |
| `DEFAULT_DECK` | `Default` | Deck selected when the page has no saved choice |
| `DATA_DIR` | `/data` | Collection and state folder |
| `STATIC_DIR` | `/app/static` in Docker | Built page to serve; unset for API only |

## API

All routes except login and health need `Authorization: Bearer <token>`.

| Method | Path | Body → response |
| --- | --- | --- |
| `POST` | `/api/login` | `{password}` → `{token}` |
| `GET` | `/api/health` | → `{ok}` |
| `GET` | `/api/decks` | → `{decks: [{id, name}], defaultDeckId}` |
| `GET` | `/api/status` | → `{sync}` |
| `POST` | `/api/lookup` | `{type, input}` → `{type, payload}` (the add-on's lookup payload; Sentence adds `sentence`) |
| `POST` | `/api/cards` | `{type, deckId, payload}` → `{added, deck, sync}`; `400` with the add-on's messages when something is missing |
| `POST` | `/api/sync` | `{forceDownload?}` → `{sync}` |

For `/api/cards`, `payload` holds what you selected and edited: Normal
`{word, results}`, Vietnamese → English `{query, results}`, Word form
`{rootWord, other}`, Word pattern the lookup fields, Sentence
`{vietnamese, sentence}`. `type` is one of `normal`, `word_form`,
`word_pattern`, `sentence`, or `vietnamese`.

## Local development

From the repository root:

```bash
pip install -r word-inbox/server/requirements-dev.txt
APP_PASSWORD=dev DATA_DIR=word-inbox/data OPENAI_API_KEY=sk-... \
  python3 -m uvicorn --factory --app-dir word-inbox/server word_inbox.app:app --port 8088 --reload

cd word-inbox/frontend
npm install
npm run dev     # http://localhost:5173, proxies /api to :8088
```

Checks:

```bash
python3 -m pytest                    # add-on and server tests
ruff check .
cd word-inbox/frontend && npm run build && npm run lint
```
