# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Anki add-on ("Anki Card Creator", formerly VIP Translate) that uses an OpenAI-compatible structured-output API to build vocabulary cards of five types: Normal, Word form, Word pattern, Sentence, and Vietnamese → English. `agent.md` holds the full contributor guide and `README.md` describes user-facing behavior. Read them before making non-trivial changes.

## Commands

```bash
python3 -m pytest                                  # all tests (config in pyproject.toml)
python3 -m pytest tests/test_audio.py::test_name   # single test
ruff check .                                       # lint (py310 target)
python3 -m compileall -q anki_card_creator
./package.sh                                       # builds anki-card-creator.ankiaddon (excludes meta.json, __pycache__)
git diff --check
(cd word-inbox/frontend && npm run build && npm run lint)   # when touching word-inbox
```

`python3 -m pytest` also runs `word-inbox/server/tests` when the server's dependencies are installed (`pip install -r word-inbox/server/requirements-dev.txt`). Without them it skips those tests.

Run all of the above before you consider a change done.

For manual testing in Anki, `~/.local/share/Anki2/addons21/anki_card_creator` must be a symlink to `anki_card_creator/` in this repo. After any code change, fully restart Anki. API keys go in Anki's add-on config, which is stored in the local `meta.json`. Never commit `meta.json` or put keys in `config.json`.

## Architecture

Flow: `__init__.py` → `bootstrap.py` (deck-overview button and Tools menu) → `ui/dialog.py` → `lookups/*`, `audio.py`, `notes/*` → `openai_client.py`.

- **Import boundary:** only `bootstrap.py` and `ui/` may import Anki's `aqt`/`anki`. Everything else must be pure so pytest can import it without Anki. Tests exercise only these pure modules.
- **Lookups (`lookups/`):** each card type has its own module with a system prompt. It calls `chat_json(...)` with a JSON schema from `lookups/schemas.py`, then checks the result with a hand-written validator in `lookups/contracts.py`, which returns a `TypedDict` payload. The schema and the validator/TypedDict for a type must be kept in sync. Validation errors (`ValueError`) are re-raised as `OpenAIError`, the only error type the UI displays.
- **Transport (`openai_client.py`):** synchronous `urllib` code for chat and TTS with no third-party dependencies. `verify_ssl` defaults to `false` on purpose, because Anki's bundled OpenSSL often fails CA checks.
- **Notes (`notes/`):** each writer module defines `NOTE_TYPE_NAME`, `FIELDS`, `CARD_FRONT`, and `CARD_BACK`. `notes/shared.py` holds the shared CSS and HTML helpers. `notes/registry.py` (`ensure_all_note_types`) creates the note types or updates them in place, which adds missing fields and overwrites templates and CSS each time the dialog opens. Vietnamese → English has no note type of its own: it reuses Normal's `VIP Translate` note type and writer.
- **Audio (`audio.py`):** TTS runs only when you click **Create cards**, never during lookup. Clips are deduplicated using keys from `audio_keys.py`.
- **UI (`ui/dialog.py`):** the `LookupDialog` switches on `CardType`. Lookups run synchronously on the UI thread. The dialog fills a panel per type, the editors in `ui/editors.py` let you edit results, and `_create_cards` validates with `create_checks.py` and writes the notes to the current deck.
- **Word Inbox (`word-inbox/`):** a single-user web version. `server/word_inbox/` is a FastAPI app that imports the add-on's pure modules (lookups, `audio.py`, `notes/*`, `create_checks.py`) and runs them against a headless collection from the `anki` pip package (`anki_store.py`), syncing with AnkiWeb. It never does a full upload, and it only does a full download when no unsynced server notes would be lost. `frontend/` is a React/Vite page whose panels mirror the dialog. Changes to the add-on's pure modules affect both, so keep the server tests passing.

## Constraints

- Keep the note type names `VIP Translate`, `VIP Word Form`, `VIP Word Pattern`, and `VIP Sentence`, since existing collections depend on them. Keep fields and templates backward-compatible, because the registry changes existing models in place.
- Don't add third-party runtime dependencies to the add-on. Word Inbox's server-only dependencies go in `word-inbox/server/requirements.txt`, pinned.
- Follow the existing style: `from __future__ import annotations`, prefix internal helpers with `_`, use `# noqa: N802` on Qt overrides, and catch broad exceptions only at UI boundaries.
- To add a new card type, touch every layer: add a schema, a contract, and a `lookups/` module; add a `notes/` writer and register it in `registry.py`; add a panel and wiring in `ui/dialog.py`; then update `README.md`.
- Update `README.md` whenever user-visible behavior or config changes, and `word-inbox/README.md` for the web app. A new card type also needs a Word Inbox panel (`frontend/src/`) and a branch in `server/word_inbox/cards.py`.
