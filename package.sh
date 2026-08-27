#!/usr/bin/env bash
# Build anki-card-creator.ankiaddon for Tools → Add-ons → Install from file…
set -euo pipefail
cd "$(dirname "$0")"

python3 - <<'PY'
import zipfile
from pathlib import Path

root = Path("anki_card_creator")
out = Path("anki-card-creator.ankiaddon")
exclude = {"meta.json", "__pycache__"}

if not root.is_dir():
    raise SystemExit(f"Missing folder: {root}")

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.name in exclude or any(part in exclude for part in rel.parts):
            continue
        zf.write(path, rel.as_posix())

print(f"Created {out.resolve()} ({out.stat().st_size} bytes)")
PY
