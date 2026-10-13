/** Ports of anki_card_creator/text.py, ui/formatting.py and notes/word_form.py. */

import type { Score, WordFormItem } from "./types";

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

const POS_ABBREV: Record<string, string> = {
  noun: "N",
  verb: "V",
  adjective: "adj",
  adverb: "adv",
  preposition: "prep",
  conjunction: "conj",
  interjection: "interj",
  pronoun: "pron",
  determiner: "det",
};

function posAbbrev(pos: string): string {
  const cleaned = pos.trim();
  return cleaned ? (POS_ABBREV[cleaned.toLowerCase()] ?? cleaned) : "?";
}

function posCount(count: number, abbrev: string): string {
  return abbrev.length <= 1 ? `${count}${abbrev}` : `${count} ${abbrev}`;
}

/** One card per part of speech among the checked forms. */
export function wordFormSummaries(root: WordFormItem, others: WordFormItem[]): string[] {
  const groups = new Map<string, WordFormItem[]>();
  for (const item of others) {
    const key = item.type.trim().toLowerCase() || "?";
    groups.set(key, [...(groups.get(key) ?? []), item]);
  }
  const rootLabel = `${root.word} (${posAbbrev(root.type)})`;
  return [...groups.values()].map(
    (items) => `${rootLabel}, ${posCount(items.length, posAbbrev(items[0].type))}`,
  );
}
