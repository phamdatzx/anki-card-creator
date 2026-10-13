import importlib.util
import sys
from pathlib import Path

SERVER = Path(__file__).parents[1]
REPO = SERVER.parents[1]
for path in (SERVER, REPO):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# The server needs its own requirements; the add-on tests must still run
# without them, so skip collecting this directory when they are missing.
_MISSING = [
    name
    for name in ("anki", "fastapi", "httpx")
    if sys.modules.get(name, True) is None or importlib.util.find_spec(name) is None
]
collect_ignore_glob = ["test_*.py"] if _MISSING else []
