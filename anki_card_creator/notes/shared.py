from __future__ import annotations

from html import escape
from typing import Any

CARD_CSS = """\
.card {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 18px;
  line-height: 1.45;
  color: #1a1a1a;
  background: #fafafa;
  text-align: left;
  padding: 1.25em 1.5em;
}
.nightMode .card { color: #ececec; background: #2b2b2b; }

.prompt {
  text-align: center;
  padding: 0.5em 0 0.25em;
}
.prompt-root {
  font-size: 1.35em;
  font-weight: 650;
  margin-bottom: 0.45em;
}
.prompt-target {
  display: inline-block;
  margin-top: 0.35em;
  padding: 0.25em 0.7em;
  border-radius: 6px;
  background: #e8eef5;
  font-size: 1.15em;
  font-weight: 650;
  letter-spacing: 0.02em;
}
.nightMode .prompt-target { background: #3a4554; }

.badge {
  display: inline-block;
  margin-left: 0.25em;
  padding: 0.05em 0.4em;
  border-radius: 4px;
  background: #ececec;
  font-size: 0.72em;
  font-weight: 600;
  vertical-align: middle;
  color: #444;
}
.nightMode .badge { background: #444; color: #ddd; }

.pos-line {
  text-align: center;
  margin-bottom: 0.6em;
}
.definition-prompt {
  text-align: center;
  font-size: 1.15em;
  line-height: 1.5;
}

.gap-prompt {
  text-align: center;
  font-size: 1.35em;
  font-weight: 600;
  letter-spacing: 0.01em;
  line-height: 1.55;
  white-space: pre-wrap;
}

.divider {
  border: 0;
  border-top: 1px solid #d0d0d0;
  margin: 1.1em 0;
}
.nightMode .divider { border-top-color: #555; }

.section {
  margin: 0.85em 0;
  padding: 0.7em 0.9em;
  border-radius: 8px;
  background: #f0f0f0;
  border: 1px solid #e2e2e2;
}
.nightMode .section {
  background: #333;
  border-color: #444;
}
.section-label {
  display: block;
  margin-bottom: 0.35em;
  font-size: 0.72em;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: #666;
}
.nightMode .section-label { color: #aaa; }

.section-word .value {
  font-size: 1.4em;
  font-weight: 700;
}
.section-meta .meta-row {
  margin: 0.2em 0;
  color: #444;
}
.nightMode .section-meta .meta-row { color: #ccc; }

.section-answer .value {
  font-size: 1.35em;
  font-weight: 700;
  color: #0b5;
}
.nightMode .section-answer .value { color: #5d5; }

.family-item {
  padding: 0.55em 0;
  border-top: 1px solid #ddd;
}
.family-item:first-child { border-top: 0; padding-top: 0; }
.nightMode .family-item { border-top-color: #4a4a4a; }
.family-word {
  font-size: 1.05em;
  font-weight: 650;
}
.family-special {
  margin-top: 0.25em;
  font-size: 0.92em;
  color: #555;
}
.nightMode .family-special { color: #bbb; }
.family-ipa {
  margin-top: 0.2em;
  font-size: 0.88em;
  color: #666;
}
.nightMode .family-ipa { color: #bbb; }
.audio-control {
  height: 1.75em;
  max-width: 12em;
  vertical-align: middle;
}

.examples-list {
  margin: 0.2em 0 0;
  padding-left: 1.15em;
}
.examples-list li { margin: 0.25em 0; }
"""


def join_values(values: Any) -> str:
    if not values:
        return ""
    if isinstance(values, str):
        return values
    return ", ".join(str(value) for value in values if value)


def examples_html(values: Any) -> str:
    if not values:
        return ""
    items = [values] if isinstance(values, str) and values.strip() else values
    cleaned = [str(value) for value in items if value]
    if not cleaned:
        return ""
    return '<ul class="examples-list">' + "".join(
        f"<li>{item}</li>" for item in cleaned
    ) + "</ul>"


def audio_control(sound_tag: str) -> str:
    if not sound_tag.startswith("[sound:") or not sound_tag.endswith("]"):
        return ""
    filename = sound_tag[7:-1]
    if not filename:
        return ""
    return (
        '<audio class="audio-control" controls preload="none" '
        f'src="{escape(filename, quote=True)}"></audio>'
    )
