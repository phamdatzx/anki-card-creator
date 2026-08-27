# VIP Translate

Anki add-on: create vocabulary cards from four card types — Normal (WordsAPI or LLM), Phrasal verb, Word form, and Word pattern (OpenAI).

## Install (development)

Prefer a **symlink** so edits in this repo load after an Anki restart.

1. Open Anki → **Tools → Add-ons → View Files** (opens `addons21`; if an add-on is selected, go up one level).
2. Symlink the `vip_translate` folder from this repo into `addons21` as `vip_translate`:

### Linux / macOS

```bash
ln -s /path/to/anki-card-creator/vip_translate \
  ~/.local/share/Anki2/addons21/vip_translate
```

On macOS, `addons21` is usually `~/Library/Application Support/Anki2/addons21`.

### Windows

Run **Command Prompt** or **PowerShell as Administrator** (or enable **Settings → System → For developers → Developer Mode** so admin is not required), then:

**Command Prompt:**

```cmd
mklink /D "%APPDATA%\Anki2\addons21\vip_translate" "C:\path\to\anki-card-creator\vip_translate"
```

**PowerShell:**

```powershell
New-Item -ItemType SymbolicLink `
  -Path "$env:APPDATA\Anki2\addons21\vip_translate" `
  -Target "C:\path\to\anki-card-creator\vip_translate"
```

Replace `C:\path\to\anki-card-creator` with the path to your clone of this repo.

3. Fully quit and restart Anki.

If Anki’s add-ons folder differs (e.g. Flatpak on Linux), use the path shown by **View Files**.

## Usage

1. Open a deck (deck overview screen).
2. Click **VIP Translate** in the bottom bar (or **Tools → VIP Translate…**).
3. Choose a **card type**:
   - **Normal** — choose **WordsAPI** (default) or **LLM**; check definitions to keep (double-click to edit).
   - **Phrasal verb** — OpenAI senses for a phrasal verb; same select/edit flow.
   - **Word form** — OpenAI word family; check related forms; **one card per POS type** (e.g. nouns card + verbs card).
   - **Word pattern** — OpenAI gap fill (e.g. `make a decision` → `A ___ a decision`).
4. **Look up** → review/edit → **Create cards** (dialog stays open for more lookups).

Cards go into the **currently selected deck**.

### Note types

| Card type | Note type | Front | Back |
| --- | --- | --- | --- |
| Normal | `VIP Translate` | POS + definition | word, pronunciation, syllables, synonyms, examples |
| Phrasal verb | `VIP Phrasal Verb` | POS + definition | phrasal verb, synonyms, examples |
| Word form | `VIP Word Form` | e.g. `able (adj), 2N` (one card per type) | root + forms of that type |
| Word pattern | `VIP Word Pattern` | gap sentence | answer, full pattern, explanation, examples |

## Config

**Tools → Add-ons → VIP Translate → Config** — set your own keys (not stored in this repo):

```json
{
  "rapidapi_key": "YOUR_RAPIDAPI_KEY",
  "rapidapi_host": "wordsapiv1.p.rapidapi.com",
  "verify_ssl": false,
  "openai_api_key": "YOUR_OPENAI_API_KEY",
  "openai_model": "gpt-5-mini",
  "openai_base_url": "https://api.openai.com/v1"
}
```

| Key | Purpose |
| --- | --- |
| `rapidapi_key` | Required for **Normal** with WordsAPI. RapidAPI WordsAPI key |
| `rapidapi_host` | API host (default `wordsapiv1.p.rapidapi.com`) |
| `verify_ssl` | Certificate verification (default `false`; Anki’s OpenSSL often fails CA checks that Postman passes) |
| `openai_api_key` | Required for **Normal (LLM)**, **Phrasal verb**, **Word form**, **Word pattern** |
| `openai_model` | OpenAI model (default `gpt-5-mini`) |
| `openai_base_url` | API base URL (default OpenAI; change for compatible proxies) |

## Layout

```
vip_translate/
  __init__.py      # overview button + Tools menu
  api.py           # WordsAPI client
  llm.py           # OpenAI structured-output client
  prompts.py       # LLM prompts + JSON schemas
  cards.py         # note types + add notes
  dialog.py        # type picker / lookup / create UI
  config.json      # default API settings
  manifest.json
```

## Package for sharing

```bash
cd vip_translate && zip -r ../vip_translate.ankiaddon *
```

Then **Tools → Add-ons → Install from file…**. Remove `__pycache__` first if present.
