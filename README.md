# VIP Translate

Anki add-on: look up a word (WordsAPI), pick definitions, and add cards to the current deck.

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
3. Enter a word → **Look up**.
4. Check the definitions you want → **Create cards**.

Cards go into the **currently selected deck**. The add-on creates/updates a note type named `VIP Translate` (Word, Pronunciation, SyllableCount, PartOfSpeech, Definition, Synonyms, Examples).

## Config

**Tools → Add-ons → VIP Translate → Config** — set your own RapidAPI key (not stored in this repo):

```json
{
  "rapidapi_key": "YOUR_RAPIDAPI_KEY",
  "rapidapi_host": "wordsapiv1.p.rapidapi.com",
  "verify_ssl": false
}
```

| Key | Purpose |
| --- | --- |
| `rapidapi_key` | Required. Your RapidAPI WordsAPI key |
| `rapidapi_host` | API host (default `wordsapiv1.p.rapidapi.com`) |
| `verify_ssl` | Certificate verification (default `false`; Anki’s OpenSSL often fails CA checks that Postman passes) |

## Layout

```
vip_translate/
  __init__.py      # overview button + Tools menu
  api.py           # WordsAPI client
  cards.py         # note type + add notes
  dialog.py        # lookup / definition picker UI
  config.json      # default API settings
  manifest.json
```

## Package for sharing

```bash
cd vip_translate && zip -r ../vip_translate.ankiaddon *
```

Then **Tools → Add-ons → Install from file…**. Remove `__pycache__` first if present.
