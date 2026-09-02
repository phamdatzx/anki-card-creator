# Anki Card Creator

Anki add-on for creating vocabulary cards from three card types — **Normal**,
**Word form**, and **Word pattern** — powered by OpenAI.

## Install (development)

Prefer a **symlink** so edits in this repo load after an Anki restart.

1. Open Anki → **Tools → Add-ons → View Files** (opens `addons21`; if an add-on is selected, go up one level).
2. Remove any old `vip_translate` symlink if you used the previous name.
3. Symlink this package:

```bash
ln -s /home/phamdatzx/projects/anki-card-creator/anki_card_creator \
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
| **Normal** | A word or phrasal verb | OpenAI | One card per selected definition |
| **Word form** | Any family member (e.g. `neatly`) | OpenAI | LLM picks true root (`neat`) + related forms; one card **per POS group** |
| **Word pattern** | A collocation / pattern | OpenAI | One gap-fill card |

#### Normal

- Enter a single word or a phrasal verb. OpenAI returns dictionary-style
  senses; phrasal-verb senses are labeled accordingly.
- Each sense includes **popularity** and **difficulty** (1–5) shown on the
  list before you create cards.
- Each card back includes an editable Vietnamese meaning for its selected sense.
- Every sense includes editable standard American English **IPA**, shown on the card back.
- Double-click a definition to edit it (including scores) before creating cards.

#### Word form

- Type any form in the family (root or derived). OpenAI chooses the **true root** (e.g. `neatly` → root `neat`) and returns related forms, each with **popularity** and **difficulty** (1–5).
- Check related forms to include; uncheck ones you do not want.
- Double-click a form to edit word, type, special definition, or scores.
- The card back includes the root word's editable Vietnamese meaning.
- Root and related forms include editable standard American English **IPA**; root IPA appears in the root section, and each form’s IPA appears beside that form.
- Creates **separate cards per POS type** — e.g. `able (adj), 2N` → one card for 2 nouns; `able (adj), 1V` → one card for 1 verb.
- On the card **back**, **related forms appear first**, then the root word and root definition.

### Pronunciation audio

- Normal cards speak the revealed word or phrasal verb on the answer side. Each
  selected definition receives its own clip, guided by its part of speech,
  definition, and first example so homographs can use the correct pronunciation.
- Word form cards play the resolved root word on the front. On the answer side, root and related-form audio use click-only controls; a card with three nouns has one control for each noun, in display order.
- Word Form TTS uses the LLM-provided IPA, part of speech, and definition to select the intended standard American English pronunciation.
- TTS is requested only after you click **Create cards**, so abandoned lookups
  incur no audio cost. Normal uses one clip per unique selected sense; Word Form
  creates its root clip once and one MP3 for each distinct selected form, reused
  if it appears more than once.

#### Word pattern

- OpenAI builds a gap-fill in context (1–2 sentences).
- **Always** hides the entire English pattern.
- Puts the **Vietnamese meaning** in the gap instead (e.g. `She (đưa ra quyết định) to quit her job.`).
- Edit gap, Vietnamese, answer, pattern, explanation, and examples before creating one card.

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
| Normal | `VIP Translate` | part of speech + definition | word, Vietnamese meaning, audio, synonyms, examples |
| Word form | `VIP Word Form` | e.g. `able (adj), 2N` + root audio | related forms with sequential form audio, then root + Vietnamese meaning + definition |
| Word pattern | `VIP Word Pattern` | gap sentence with Vietnamese meaning | answer, Vietnamese, pattern, explanation, examples |

Card templates use styled sections (labels, badges, example lists) with light and night mode support. Opening the add-on syncs note type templates to the latest version.

## Config

**Tools → Add-ons → Anki Card Creator → Config**

Copy the defaults below and fill in your own keys. Keys are **not** stored in this repo.

```json
{
  "verify_ssl": false,
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "openai_model": "gpt-5-mini",
  "openai_base_url": "https://api.openai.com/v1",
  "openai_tts_model": "gpt-4o-mini-tts",
  "openai_tts_voice": "alloy"
}
```

### Config reference

| Key | Required for | Description |
| --- | --- | --- |
| `verify_ssl` | All HTTP requests | `true` = verify TLS certificates; `false` = skip verification (default). Anki’s bundled OpenSSL often fails CA checks that work in Postman or curl; set `false` if you see `CERTIFICATE_VERIFY_FAILED`. |
| `openai_api_key` | All card types | OpenAI API key (or compatible provider key). |
| `openai_model` | All LLM card types | Model name. Default: `gpt-5-mini`. Any model that supports structured JSON output works. |
| `openai_base_url` | All LLM card types | API base URL. Default: `https://api.openai.com/v1`. Change for OpenAI-compatible proxies or local servers. |
| `openai_tts_model` | Normal, Word form | Text-to-speech model. Default: `gpt-4o-mini-tts`. |
| `openai_tts_voice` | Normal, Word form | OpenAI TTS voice. Default: `alloy`. |

### Which keys do I need?

| What you use | Keys to set |
| --- | --- |
| Any card type | `openai_api_key` |
| Change the TTS voice/model | `openai_tts_voice` / `openai_tts_model` (optional) |

## Project layout

```
anki_card_creator/
  __init__.py      # minimal guarded Anki entry point
  bootstrap.py     # deck overview button + Tools menu registration
  config.py        # normalized typed configuration
  openai_client.py # shared synchronous HTTP/TLS/error handling
  audio.py         # TTS instructions, deduplication, and media storage
  audio_keys.py    # shared normalized audio identity keys
  text.py          # pure text/list/score helpers
  lookups/         # per-card-type prompts, schemas, and payload contracts
  notes/           # shared CSS/registry and per-card-type note writers
  ui/              # widgets, formatting, editors, and dialog orchestration
  config.json      # default config (no secrets)
  manifest.json
tests/             # focused pure unit tests
pyproject.toml     # pytest and Ruff development configuration
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

The package script recursively includes subpackages and excludes every
`meta.json` and `__pycache__` path.

## Development verification

The add-on has no third-party runtime dependencies. Pytest and Ruff are
development-only tools:

```bash
python3 -m pytest
ruff check .
python3 -m compileall -q anki_card_creator
./package.sh
git diff --check
```

## Migrating from VIP Translate

If you previously installed the add-on as `vip_translate`:

1. Remove the old symlink: `~/.local/share/Anki2/addons21/vip_translate`
2. Symlink `anki_card_creator` as shown above
3. Restart Anki

Your existing notes and decks are unchanged. Note type names (`VIP Translate`, etc.) are kept for compatibility with cards already in your collection.
