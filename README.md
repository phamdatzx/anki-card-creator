# Anki Card Creator

Anki add-on for creating vocabulary cards from four card types — **Normal**, **Phrasal verb**, **Word form**, and **Word pattern** — powered by OpenAI.

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
| **Normal** | A single word | OpenAI | One card per selected definition |
| **Phrasal verb** | A phrasal verb | OpenAI | One card per selected sense |
| **Word form** | Any family member (e.g. `neatly`) | OpenAI | LLM picks true root (`neat`) + related forms; one card **per POS group** |
| **Word pattern** | A collocation / pattern | OpenAI | One gap-fill card |

#### Normal

- OpenAI returns dictionary-style senses. Each sense includes **popularity** and **difficulty** (1–5) shown on the list before you create cards.
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

### Pronunciation audio

- Normal and Phrasal verb cards speak the revealed word on the answer side. Each selected definition receives its own clip, guided by its part of speech, definition, and first example so homographs can use the correct pronunciation.
- Word form cards play the resolved root word on the front. The answer side plays each related form in its displayed order; a card with three nouns plays all three noun clips in sequence.
- Word Form TTS asks OpenAI for standard American English pronunciation and supplies each form’s part of speech to help select the right stress and pronunciation.
- TTS is requested only after you click **Create cards**, so abandoned lookups incur no audio cost. Normal and Phrasal use one clip per unique selected sense; Word Form creates its root clip once and one MP3 for each distinct selected form, reused if it appears more than once.

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
| Normal | `VIP Translate` | part of speech + definition | word + audio, synonyms, examples |
| Phrasal verb | `VIP Phrasal Verb` | part of speech + definition | phrasal verb + audio, synonyms, examples |
| Word form | `VIP Word Form` | e.g. `able (adj), 2N` + root audio | related forms with sequential form audio, then root + root definition |
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
| `openai_tts_model` | Normal, Phrasal verb, Word form | Text-to-speech model. Default: `gpt-4o-mini-tts`. |
| `openai_tts_voice` | Normal, Phrasal verb, Word form | OpenAI TTS voice. Default: `alloy`. |

### Which keys do I need?

| What you use | Keys to set |
| --- | --- |
| Any card type | `openai_api_key` |
| Change the TTS voice/model | `openai_tts_voice` / `openai_tts_model` (optional) |

## Project layout

```
anki_card_creator/
  __init__.py      # deck overview button + Tools menu
  api.py           # shared SSL context
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
