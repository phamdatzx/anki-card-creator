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
  __init__.py   # Anki hooks, deck button, and Tools menu
  dialog.py     # PyQt card creation UI and workflow
  llm.py        # OpenAI-compatible JSON client
  prompts.py    # LLM prompts, schemas, and lookup functions
  cards.py      # Note types, templates, and note creation
  config.json   # Default configuration; no secrets
  manifest.json # Add-on metadata
package.sh      # Builds the .ankiaddon archive
README.md       # User and development documentation
```

The primary flow is:

```text
__init__.py -> dialog.py -> prompts.py + llm.py -> cards.py
```

Keep UI, lookup, and note-persistence responsibilities separated along these
boundaries.

## Conventions

- Target the Python version bundled with supported Anki releases.
- Use `from __future__ import annotations` and modern type hints, matching the
  existing modules.
- Prefix internal helpers with `_`.
- Use `LlmError` for user-facing lookup failures.
- Qt override names may use `# noqa: N802`; keep broad exception handling
  limited to user-facing UI boundaries.
- Avoid unrelated refactors, particularly in the large `dialog.py` module.

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

1. Add its schema, prompt, and `lookup_*` function in `prompts.py`.
2. Add its note type fields, templates, and `add_*` function in `cards.py`;
   register it with `ensure_all_note_types()`.
3. Add the enum/UI panel plus lookup and creation handlers in `dialog.py`.
4. Update `README.md` with user-facing behavior and configuration.

## Verification

There is currently no automated test suite, linter configuration, or CI.
Run the checks relevant to a change:

```bash
python3 -m py_compile anki_card_creator/*.py
./package.sh
```

For UI and Anki integration changes, install via a symlink or add-on package,
configure API keys through Anki's add-on config, and fully restart Anki before
testing. Remove generated `__pycache__` directories before packaging if they
exist.

## Scope discipline

- Keep changes focused on the requested behavior.
- Update `README.md` for changed user-visible features or configuration.
- Treat `PLAN_MULTI_FEATURE.md` as historical planning context, not a source
  of current requirements.
