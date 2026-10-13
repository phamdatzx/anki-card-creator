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
  docker-compose.yml          build and run locally or by hand
  deploy/docker-compose.yml   what the deploy workflow puts on the VPS
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

## Deploy to a VPS with GitHub Actions

Two workflows live in `.github/workflows/`:

- **`ci.yml`** runs on every pull request: Ruff, pytest (add-on and server),
  packaging of the add-on, and the frontend build and lint.
- **`deploy.yml`** runs on every push to `main` that touches
  `anki_card_creator/`, `word-inbox/`, or the workflows. You can also start it
  by hand under **Actions → Deploy Word Inbox → Run workflow**. It runs CI,
  builds the image, pushes it to GHCR as `ghcr.io/<owner>/word-inbox:<commit>`
  (and `:latest`), then connects to the VPS over SSH. There it pulls that exact
  tag, restarts the container, and waits for `/api/health`.

The deploy only replaces the container. Your `.env` and `data/` folder on the
VPS are never touched.

### One-time VPS setup

1. Install Docker Engine with the Compose plugin (`docker compose version`
   must work), and create a deploy user that can run Docker:

   ```bash
   sudo adduser --disabled-password deploy
   sudo usermod -aG docker deploy
   ```

2. Create a key pair just for deploys, on your own machine:

   ```bash
   ssh-keygen -t ed25519 -N "" -C "word-inbox deploy" -f word-inbox-deploy
   ```

   Append `word-inbox-deploy.pub` to `/home/deploy/.ssh/authorized_keys` on
   the VPS.

3. As `deploy`, create the app folder and its settings. The workflow
   refuses to deploy without `.env`:

   ```bash
   mkdir -p ~/word-inbox/data
   nano ~/word-inbox/.env    # contents: see .env.example
   chmod 600 ~/word-inbox/.env
   ```

4. Put a TLS reverse proxy in front of `127.0.0.1:8088` (see the Caddy
   example above).

### GitHub secrets

Add these under **Settings → Secrets and variables → Actions → Repository
secrets**. You can also put them on the `production` environment, which lets
you require an approval before each deploy.

| Secret | Required | Value |
| --- | --- | --- |
| `VPS_SSH_KEY` | yes | The private key, i.e. the whole contents of `word-inbox-deploy` |
| `VPS_HOST` | yes | VPS IP or host name |
| `VPS_USER` | yes | `deploy` |
| `VPS_PORT` | no | SSH port, default `22` |
| `VPS_DEPLOY_PATH` | no | App folder, default `word-inbox` (relative to the user's home, or absolute) |
| `VPS_KNOWN_HOSTS` | recommended | Output of `ssh-keyscan -p <port> <host>`, checked from a machine you trust. Without it, each run trusts whatever host key it sees. |

No registry password is needed. The workflow pushes and pulls with the run's
own short-lived `GITHUB_TOKEN`, logs the VPS in for the pull only, and logs
it out again.

### Operating it

On the VPS, in `~/word-inbox`:

```bash
docker compose ps
docker compose logs -f app
docker compose restart app     # e.g. after editing .env
```

To roll back, open an older successful **Deploy Word Inbox** run and click
**Re-run all jobs**. That rebuilds that commit's image and deploys it. You can
also set `image:` in the VPS's `docker-compose.yml` to an older
`:<commit>` tag and run `docker compose up -d`.

The image is built for `linux/amd64` only, the platform the `anki` wheel
targets in this setup.

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
