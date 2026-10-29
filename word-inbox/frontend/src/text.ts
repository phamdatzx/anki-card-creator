/** Ports of anki_card_creator/text.py and ui/formatting.py. */

import type { Score } from "./types";

export function asText(values: string[] | undefined, multiline = false): string {
  return (values ?? []).filter(Boolean).join(multiline ? "\n" : ", ");
}

export function splitList(text: string, multiline = false): string[] {
  const cleaned = text.trim();
  if (!cleaned) {
    return [];
  }
  const parts =
    multiline && cleaned.includes("\n") ? cleaned.split(/\r?\n/) : cleaned.split(",");
  return parts.map((part) => part.trim()).filter(Boolean);
}

/** Blank or out-of-range scores become null, which the server accepts. */
export function parseScore(text: string): Score {
  const value = Number.parseInt(text.trim(), 10);
  return Number.isInteger(value) && value >= 1 && value <= 5 ? value : null;
}

export function scoreText(score: Score): string {
  return score === null ? "" : String(score);
}

export function scoresCompact(item: { popularity: Score; difficulty: Score }): string {
  const parts = [];
  if (item.popularity !== null) {
    parts.push(`pop ${item.popularity}/5`);
  }
  if (item.difficulty !== null) {
    parts.push(`hard ${item.difficulty}/5`);
  }
  return parts.join(" · ");
}
