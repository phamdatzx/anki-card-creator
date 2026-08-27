# Anki Card Creator

Anki add-on for creating vocabulary cards from four card types — **Normal** (WordsAPI or LLM), **Phrasal verb**, **Word form**, and **Word pattern** (OpenAI).

## Install (development)

Prefer a **symlink** so edits in this repo load after an Anki restart.

1. Open Anki → **Tools → Add-ons → View Files** (opens `addons21`; if an add-on is selected, go up one level).
2. Remove any old `vip_translate` symlink if you used the previous name.
3. Symlink this package:

```bash
ln -s /home/datjax/projects/vip-translate/anki_card_creator \
  ~/.local/share/Anki2/addons21/anki_card_creator
```

4. Fully quit and restart Anki.

If Anki’s add-ons folder differs (e.g. Flatpak on Linux), use the path shown by **View Files**.

## Usage

1. Open a deck (deck overview screen).
2. Click **Anki Card Creator** in the bottom bar (or **Tools → Anki Card Creator…**).
3. Choose a **card type** and look up your input.
4. Review / edit results, check what to include, then **Create cards** (or press **Ctrl+Enter**).
5. The dialog stays open and clears the previous word after a successful create so you can add more cards quickly.

### Card types

| Type | Input | Source | What you get |
| --- | --- | --- | --- |
| **Normal** | A single word | **WordsAPI** (default) or **LLM** | One card per selected definition |
| **Phrasal verb** | A phrasal verb | OpenAI | One card per selected sense |
| **Word form** | Any family member (e.g. `neatly`) | OpenAI | LLM picks true root (`neat`) + related forms; one card **per POS group** |
| **Word pattern** | A collocation / pattern | OpenAI | One gap-fill card |

#### Normal

- Pick **Source → WordsAPI** (default) or **LLM**.
- **WordsAPI** returns dictionary definitions with pronunciation and syllable count when available.
- **LLM** uses OpenAI for dictionary-style senses (requires `openai_api_key`). Each sense includes **popularity** and **difficulty** (1–5) shown on the list before you create cards.
- Double-click a definition to edit it (including scores) before creating cards.

#### Phrasal verb

- OpenAI returns distinct senses for the phrasal verb; each sense has its own **popularity** and **difficulty** (1–5).
- Same select / double-click to edit / create flow as Normal.

#### Word form

- Type any form in the family (root or derived). OpenAI chooses the **true root** (e.g. `neatly` → root `neat`) and returns related forms, each with **popularity** and **difficulty** (1–5).
- Check related forms to include; uncheck ones you do not want.
- Double-click a form to edit word, type, special definition, or scores.
- Creates **separate cards per POS type** — e.g. `able (adj), 2N` → one card for 2 nouns; `able (adj), 1V` → one card for 1 verb.
- On the card **back**, **related forms appear first**, then the root word and root definition.

#### Word pattern

- OpenAI builds a gap-fill question (e.g. `make a decision` → `She __ a decision to quit her job`).
- Edit gap, answer, pattern, explanation, and examples before creating one card.

### UI shortcuts & workflow

| Action | How |
| --- | --- |
| Look up | **Look up** button or **Enter** in the input field |
| Create cards | **Create cards** button or **Ctrl+Enter** |
| Edit a definition / form | Double-click the list item |
| After create | Input and results clear automatically; dialog stays open |

Cards are added to the **currently selected deck**.

### Note types

| Card type | Note type | Front | Back |
| --- | --- | --- | --- |
| Normal | `VIP Translate` | part of speech + definition | word, pronunciation, syllables, synonyms, examples |
| Phrasal verb | `VIP Phrasal Verb` | part of speech + definition | phrasal verb, synonyms, examples |
| Word form | `VIP Word Form` | e.g. `able (adj), 2N` | related forms first, then root + root definition |
| Word pattern | `VIP Word Pattern` | gap sentence | answer, full pattern, explanation, examples |

Card templates use styled sections (labels, badges, example lists) with light and night mode support. Opening the add-on syncs note type templates to the latest version.

## Config

**Tools → Add-ons → Anki Card Creator → Config**

Copy the defaults below and fill in your own keys. Keys are **not** stored in this repo.

```json
{
  "rapidapi_key": "YOUR_RAPIDAPI_KEY",
  "rapidapi_host": "wordsapiv1.p.rapidapi.com",
  "verify_ssl": false,
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "openai_model": "gpt-4.1-mini",
  "openai_base_url": "https://api.openai.com/v1"
}
```

### Config reference

| Key | Required for | Description |
| --- | --- | --- |
| `rapidapi_key` | Normal (**WordsAPI**) | RapidAPI key for [WordsAPI](https://rapidapi.com/dpventures/api/wordsapiv1). Leave empty if you only use LLM for Normal. |
| `rapidapi_host` | Normal (WordsAPI) | API host. Default: `wordsapiv1.p.rapidapi.com`. Change only if your RapidAPI subscription uses a different host. |
| `verify_ssl` | All HTTP requests | `true` = verify TLS certificates; `false` = skip verification (default). Anki’s bundled OpenSSL often fails CA checks that work in Postman or curl; set `false` if you see `CERTIFICATE_VERIFY_FAILED`. |
| `openai_api_key` | Normal (**LLM**), Phrasal verb, Word form, Word pattern | OpenAI API key (or compatible provider key). |
| `openai_model` | All LLM card types | Model name. Default: `gpt-5-mini`. Any model that supports structured JSON output works. |
| `openai_base_url` | All LLM card types | API base URL. Default: `https://api.openai.com/v1`. Change for OpenAI-compatible proxies or local servers. |

### Which keys do I need?

| What you use | Keys to set |
| --- | --- |
| Normal with WordsAPI only | `rapidapi_key` |
| Normal with LLM only | `openai_api_key` |
| Normal with both sources | `rapidapi_key` + `openai_api_key` |
| Phrasal verb / Word form / Word pattern | `openai_api_key` |
| Everything | All keys above |

## Project layout

```
anki_card_creator/
  __init__.py      # deck overview button + Tools menu
  api.py           # WordsAPI client
  llm.py           # OpenAI structured-output client
  prompts.py       # LLM prompts + JSON schemas
  cards.py         # note types, templates, add notes
  dialog.py        # card type picker, lookup, create UI
  config.json      # default config (no secrets)
  manifest.json
```

## Package for sharing

From the repo root:

```bash
./package.sh
```

Or manually:

```bash
cd anki_card_creator && zip -r ../anki-card-creator.ankiaddon . -x meta.json -x "__pycache__/*"
```

This creates `anki-card-creator.ankiaddon` in the repo root (without `meta.json`, so your local API keys are not included).

### Install from file in Anki

1. **Tools → Add-ons → Install from file…**
2. Select `anki-card-creator.ankiaddon`
3. Restart Anki when prompted
4. **Tools → Add-ons → Anki Card Creator → Config** — add your API keys

Remove `__pycache__` before packaging if present.

## Migrating from VIP Translate

If you previously installed the add-on as `vip_translate`:

1. Remove the old symlink: `~/.local/share/Anki2/addons21/vip_translate`
2. Symlink `anki_card_creator` as shown above
3. Restart Anki

Your existing notes and decks are unchanged. Note type names (`VIP Translate`, etc.) are kept for compatibility with cards already in your collection.
