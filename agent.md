# Agent Guide

## Project

This repository is an Anki add-on for creating vocabulary cards. It supports
Normal, Word form, and Word pattern card types through an OpenAI-compatible
structured-output API. Normal accepts either a word or a phrasal verb.

The add-on runs inside Anki and relies on Anki-bundled `anki` and `aqt`
modules. Do not add third-party Python dependencies without a clear need.

## Repository layout

```text
anki_card_creator/
  __init__.py       # minimal guarded entry point
  bootstrap.py      # Anki hooks, deck button, and Tools menu
  config.py         # typed configuration and gpt-5-mini defaults
  openai_client.py  # synchronous OpenAI chat/TTS transport
  audio.py          # TTS instructions, deduplication, and media storage
  audio_keys.py     # shared normalized audio identity keys
  text.py           # pure text/list/score conversions
  lookups/          # payload contracts, schemas, and lookup use cases
  notes/            # shared CSS/registry and note writers
  ui/               # widgets, formatting, editors, and main dialog
  config.json       # Default configuration; no secrets
  manifest.json     # Add-on metadata
tests/               # pure unit tests
pyproject.toml       # pytest/Ruff development configuration
package.sh      # Builds the .ankiaddon archive
README.md       # User and development documentation
```

The primary flow is:

```text
__init__.py -> bootstrap.py -> ui/dialog.py
ui/dialog.py -> lookups/* + audio.py + notes/*
lookups/* + audio.py -> openai_client.py
```

Keep UI, lookup, and note-persistence responsibilities separated along these
boundaries.

## Conventions

- Target the Python version bundled with supported Anki releases.
- Use `from __future__ import annotations` and modern type hints, matching the
  existing modules.
- Prefix internal helpers with `_`.
- Use `OpenAIError` for user-facing lookup failures.
- Qt override names may use `# noqa: N802`; keep broad exception handling
  limited to user-facing UI boundaries.
- Keep pure helpers importable without the Anki-provided `aqt` and `anki`
  modules. Restrict those imports to `bootstrap.py` and `ui/`.

## Compatibility and security

- Preserve these note type names: `VIP Translate`, `VIP Word Form`, and
  `VIP Word Pattern`. Existing Anki collections depend on them.
- Keep note fields and templates backward-compatible unless migration behavior
  is intentionally implemented.
- Never commit API keys, local `meta.json`, `.env` files, or generated
  `.ankiaddon` archives.
- `meta.json` is Anki's local configuration override and is excluded from
  packages.
- The default `verify_ssl: false` exists because Anki's bundled OpenSSL can
  fail certificate validation; do not change it casually.

## Changing or adding card types

For a new card type, update all applicable layers:

1. Add its payload contract/schema and a module in `lookups/`.
2. Add a writer module in `notes/` and register it in `notes/registry.py`.
3. Add its UI panel plus orchestration in `ui/dialog.py`.
4. Update `README.md` with user-facing behavior and configuration.

## Verification

Run the complete local verification workflow:

```bash
python3 -m pytest
ruff check .
python3 -m compileall -q anki_card_creator
./package.sh
git diff --check
```

For UI and Anki integration changes, install via a symlink or add-on package,
configure API keys through Anki's add-on config, and fully restart Anki before
testing. The package script recursively includes subpackages and excludes local
`meta.json` and `__pycache__` paths.

## Scope discipline

- Keep changes focused on the requested behavior.
- Update `README.md` for changed user-visible features or configuration.
